import os
import gzip

def compress_json_to_gz(input_dir="stores_by_region"):
    # 디렉토리 내 모든 파일 목록 가져오기
    all_files = os.listdir(input_dir)
    json_files = [f for f in all_files if f.endswith('.json')]
    gz_files = [f for f in all_files if f.endswith('.json.gz')]

    for json_file in json_files:
        # .gz 파일이 이미 존재하는지 확인
        gz_file = json_file + '.gz'
        if gz_file in gz_files:
            print(f"⏭️ {json_file}에 대한 {gz_file}가 이미 존재하므로 스킵")
            continue

        # .json 파일 경로
        json_path = os.path.join(input_dir, json_file)
        # .gz 파일 경로
        gz_path = os.path.join(input_dir, gz_file)

        try:
            # .json을 읽고 gzip으로 압축
            with open(json_path, 'rb') as f_in:
                with gzip.open(gz_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            print(f"✅ {json_file}를 {gz_file}로 압축 완료")
        except Exception as e:
            print(f"❌ {json_file} 압축 실패: {e}")

if __name__ == "__main__":
    import os
    os.makedirs("stores_by_region", exist_ok=True)
    compress_json_to_gz()