import csv
import json
import requests
import time
import re
import gzip
from collections import defaultdict

API_KEY = "401f9e3117d91b4a7f7dfbcf81bba69c"

def geocode_address(address):
    cleaned_address = re.sub(r'\s*\(.*?\)\s*', ' ', address)
    cleaned_address = re.sub(r'\s*(지하)?\d+[-~]?\d*층\s*', ' ', cleaned_address).strip()
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {API_KEY}"}
    params = {"query": cleaned_address}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data["documents"]:
            doc = data["documents"][0]
            region_1depth = doc["address"]["region_1depth_name"]
            return {
                "lat": float(doc["y"]), 
                "lng": float(doc["x"]), 
                "region": region_1depth
            }
        else:
            print(f"⚠️ 주소 변환 실패: {cleaned_address} - 결과 없음")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 실패: {cleaned_address} - {e}")
        return None

def process_csv_to_json(csv_file, output_dir="stores_by_region"):
    stores_by_region = defaultdict(list)
    failed_addresses = []
    
    try:
        with open(csv_file, encoding='utf-8') as f:
            reader = csv.reader(f)
            total = sum(1 for row in open(csv_file, encoding='utf-8') if row.strip())
            print(f"📊 총 {total}개 주소 처리 시작")
            
            header = next(reader)
            for i, row in enumerate(reader, 1):
                if not row or len(row) < 5:
                    print(f"⚠️ 데이터 부족 스킵 ({i}/{total}): {row}")
                    continue
                
                if len(row) == 5:
                    category, name, price, phone, address = [x.strip() for x in row]
                    main_item = ""
                    print(f"ℹ️ main_item 누락 처리 ({i}/{total}): {name} - {address}")
                else:
                    category, name, main_item, price, phone, address = [x.strip() for x in row[:6]]
                
                print(f"🔍 처리 중 ({i}/{total}): {name} - {address}")
                
                coords = geocode_address(address)
                if coords:
                    address_parts = address.split()
                    short_address = " ".join(address_parts[1:]) if len(address_parts) > 1 else address
                    store_data = [
                        name,
                        price.replace(',', ''),  # 쉼표 제거
                        coords["lat"],
                        coords["lng"],
                        category,
                        main_item,
                        phone,
                        short_address
                    ]
                    region = coords["region"].replace("특별시", "").replace("광역시", "").replace("도", "").replace(" ", "_").lower()
                    stores_by_region[region].append(store_data)
                else:
                    failed_addresses.append(address)
                
                time.sleep(0.1)
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {csv_file}")
        return
    
    for region, stores in stores_by_region.items():
        json_file = f"{output_dir}/stores_{region}.json"
        gz_file = f"{output_dir}/stores_{region}.json.gz"
        
        json_data = [
            ["// [n: name, p: price, lt: lat, lg: lng, c: category, m: main_item, ph: phone, a: address]"]
        ] + stores
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"✅ {region}: {len(stores)}개 데이터 저장 완료: {json_file}")
        
        with open(json_file, 'rb') as f_in:
            with gzip.open(gz_file, 'wb') as f_out:
                f_out.writelines(f_in)
        print(f"✅ {region}: Gzip 압축 완료: {gz_file}")
    
    if failed_addresses:
        print("❌ 변환 실패 주소:")
        for addr in failed_addresses:
            print(f"  - {addr}")

if __name__ == "__main__":
    import os
    os.makedirs("stores_by_region", exist_ok=True)
    process_csv_to_json("stores_v2-all.csv", "stores_by_region")