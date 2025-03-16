import csv
import json
import requests
import time
import re
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
            region_1depth = doc["address"]["region_1depth_name"]  # "서울특별시", "경기도" 등
            region_2depth = doc["address"]["region_2depth_name"]  # "종로구", "성남시" 등
            return {
                "lat": float(doc["y"]), 
                "lng": float(doc["x"]), 
                "region_1depth": region_1depth,
                "region_2depth": region_2depth
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
    
    with open(csv_file, encoding='utf-8') as f:
        reader = csv.reader(f)
        total = sum(1 for row in open(csv_file, encoding='utf-8') if row.strip())
        print(f"📊 총 {total}개 주소 처리 시작")
        
        header = next(reader)
        for i, row in enumerate(reader, 1):
            if not row or len(row) < 6:
                print(f"⚠️ 데이터 부족 스킵 ({i}/{total}): {row}")
                continue
            
            category, name, main_item, price, phone, address = [x.strip() for x in row]
            print(f"🔍 처리 중 ({i}/{total}): {name} - {address}")
            
            coords = geocode_address(address)
            store_data = {
                "category": category,
                "name": name,
                "main_item": main_item,
                "price": price,
                "phone": phone,
                "address": address
            }
            if coords:
                store_data.update({
                    "lat": coords["lat"],
                    "lng": coords["lng"],
                    "region_1depth": coords["region_1depth"],
                    "region_2depth": coords["region_2depth"]
                })
                region = coords["region_1depth"].replace("특별시", "").replace("광역시", "").replace("도", "").replace(" ", "_").lower()
                stores_by_region[region].append(store_data)
            else:
                store_data.update({"lat": None, "lng": None, "region_1depth": None, "region_2depth": None})
                failed_addresses.append(address)
            
            time.sleep(0.1)
    
    for region, stores in stores_by_region.items():
        json_file = f"{output_dir}/stores_{region}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(stores, f, ensure_ascii=False, indent=2)
        print(f"✅ {region}: {len(stores)}개 데이터 저장 완료: {json_file}")
    
    if failed_addresses:
        print("❌ 변환 실패 주소:")
        for addr in failed_addresses:
            print(f"  - {addr}")

if __name__ == "__main__":
    import os
    os.makedirs("stores_by_region", exist_ok=True)
    process_csv_to_json("stores.csv", "stores_by_region")