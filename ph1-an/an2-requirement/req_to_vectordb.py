"""
이미지 파일에서 텍스트를 추출하여 벡터DB에 등록하는 스크립트

입력: file/img/1650-01_요구사항정의서_v1.0_page_*.png
출력: chroma-agent 벡터DB에 데이터 등록
"""

import os
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
import easyocr

def extract_text_from_images(image_dir: str, pattern: str) -> dict:
    """이미지 파일들에서 텍스트 추출"""
    print("🔍 이미지 파일 검색 중...")
    image_path = Path(image_dir)
    image_files = sorted(image_path.glob(pattern))
    
    if not image_files:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_dir}/{pattern}")
    
    print(f"📄 발견된 이미지 파일: {len(image_files)}개")
    for img in image_files:
        print(f"  - {img.name}")
    
    # EasyOCR reader 초기화 (한국어, 영어)
    print("\n🤖 OCR 모델 로딩 중...")
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
    
    # 각 이미지에서 텍스트 추출
    extracted_data = {}
    for img_file in image_files:
        print(f"\n📖 텍스트 추출 중: {img_file.name}")
        result = reader.readtext(str(img_file))
        
        # 추출된 텍스트를 하나의 문자열로 결합
        text = '\n'.join([detection[1] for detection in result])
        extracted_data[img_file.name] = text
        
        print(f"  ✓ 추출된 텍스트 길이: {len(text)} 문자")
        print(f"  ✓ 추출된 텍스트 블록 수: {len(result)} 개")
    
    return extracted_data

def parse_ec2_info_from_text(all_text: str) -> dict:
    """텍스트에서 EC2 정보 파싱"""
    import re
    
    ec2_info = {
        'ips': set(),
        'ssh_user': None,
        'pem_path': None
    }
    
    # IP 주소 패턴 찾기 (xxx.xxx.xxx.xxx)
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ips = re.findall(ip_pattern, all_text)
    
    for ip in ips:
        # 유효한 IP인지 확인
        parts = ip.split('.')
        try:
            if all(0 <= int(p) <= 255 for p in parts):
                ec2_info['ips'].add(ip)
        except ValueError:
            continue
    
    # SSH User 찾기
    if 'ec2-user' in all_text.lower():
        ec2_info['ssh_user'] = 'ec2-user'
    elif 'ubuntu' in all_text.lower():
        ec2_info['ssh_user'] = 'ubuntu'
    
    # PEM 경로 찾기
    pem_patterns = [
        r'/[^\s]+\.pem',
        r'[^\s]+keypair\.pem'
    ]
    
    for pattern in pem_patterns:
        pem_matches = re.findall(pattern, all_text)
        if pem_matches:
            ec2_info['pem_path'] = pem_matches[0]
            break
    
    # 기본 경로 추정 (jacob.park 키워드가 있는 경우)
    if not ec2_info['pem_path'] and 'jacob' in all_text.lower() and 'park' in all_text.lower():
        ec2_info['pem_path'] = '/home/ec2-user/.ssh/jacob.park-keypair.pem'
    
    return ec2_info


def format_as_spec(extracted_data: dict) -> list:
    """추출된 텍스트에서 EC2 정보를 추출하여 지정된 포맷으로 변환"""
    print("\n📝 EC2 정보 추출 및 포맷 변환 중...")
    
    # 모든 텍스트를 하나로 합치기
    all_text = '\n\n'.join(extracted_data.values())
    
    # EC2 정보 파싱
    ec2_info = parse_ec2_info_from_text(all_text)
    
    print(f"\n🔍 추출된 EC2 정보:")
    print(f"  - IP 주소: {list(ec2_info['ips'])}")
    print(f"  - SSH User: {ec2_info['ssh_user']}")
    print(f"  - PEM 경로: {ec2_info['pem_path']}")
    
    documents = []
    ids = []
    metadatas = []
    
    # EC2 IP 정보
    if ec2_info['ips']:
        ip_list = ','.join(sorted(ec2_info['ips']))
        documents.append(f"EC2 IP 정보: {ip_list}")
        ids.append("ec2_ip_list")
        metadatas.append({
            "type": "infrastructure",
            "service": "ec2",
            "field": "ip",
            "owner": "jacob.park"
        })
        print(f"  ✓ ec2_ip_list 변환 완료")
    
    # EC2 SSH User 정보
    if ec2_info['ssh_user']:
        documents.append(f"EC2 SSH User 정보: {ec2_info['ssh_user']}")
        ids.append("ec2_ssh_user")
        metadatas.append({
            "type": "infrastructure",
            "service": "ec2",
            "field": "ssh_user",
            "owner": "jacob.park"
        })
        print(f"  ✓ ec2_ssh_user 변환 완료")
    
    # EC2 PEM 경로
    if ec2_info['pem_path']:
        documents.append(f"EC2 PEM 경로: {ec2_info['pem_path']}")
        ids.append("ec2_pem_path")
        metadatas.append({
            "type": "infrastructure",
            "service": "ec2",
            "field": "pem_path",
            "owner": "jacob.park"
        })
        print(f"  ✓ ec2_pem_path 변환 완료")
    
    if not documents:
        print("  ⚠️  추출된 EC2 정보가 없습니다.")
    
    return documents, ids, metadatas

def clear_vectordb(collection):
    """벡터DB의 기존 데이터 삭제"""
    print("\n🗑️  벡터DB 기존 데이터 삭제 중...")
    
    try:
        # 모든 문서 ID 가져오기
        all_data = collection.get()
        if all_data['ids']:
            collection.delete(ids=all_data['ids'])
            print(f"  ✓ {len(all_data['ids'])}개 문서 삭제 완료")
        else:
            print("  ℹ️  삭제할 데이터가 없습니다")
    except Exception as e:
        print(f"  ⚠️  삭제 중 오류 발생: {e}")

def register_to_vectordb(documents: list, ids: list, metadatas: list):
    """벡터DB에 데이터 등록"""
    print("\n💾 벡터DB 연결 중...")
    
    # Persistent DB 연결
    client = chromadb.PersistentClient(path="./chroma-agent/chroma_store")
    
    # 임베딩 함수
    sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # 컬렉션 가져오기 또는 생성
    collection = client.get_or_create_collection(
        name="agent_knowledge",
        embedding_function=sentence_ef
    )
    
    # 기존 데이터 삭제
    clear_vectordb(collection)
    
    # 새 데이터 등록
    print("\n📥 벡터DB에 데이터 등록 중...")
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"  ✅ {len(documents)}개 문서 등록 완료")
    
    return collection

def test_search(collection):
    """등록된 데이터 검색 테스트"""
    print("\n🔎 검색 테스트 수행 중...")
    
    test_queries = [
        "EC2 접속 정보",
        "IP 주소는?",
        "PEM 파일 경로"
    ]
    
    for query in test_queries:
        print(f"\n  질문: {query}")
        result = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        if result['documents'] and result['documents'][0]:
            for i, doc in enumerate(result['documents'][0], 1):
                print(f"    {i}. {doc}")
                if result['metadatas'] and result['metadatas'][0]:
                    print(f"       메타데이터: {result['metadatas'][0][i-1]}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("이미지 → EC2 정보 추출 → 벡터DB 등록 프로세스 시작")
    print("=" * 60)
    
    try:
        # 1. 이미지에서 텍스트 추출
        image_dir = "file/img"
        pattern = "1650-01_요구사항정의서_v1.0_page_*.png"
        extracted_data = extract_text_from_images(image_dir, pattern)
        
        # 2. EC2 정보 추출 및 포맷 변환
        documents, ids, metadatas = format_as_spec(extracted_data)
        
        if not documents:
            print("\n❌ 추출된 EC2 정보가 없습니다. 처리를 중단합니다.")
            return 1
        
        # 3. 벡터DB에 등록
        collection = register_to_vectordb(documents, ids, metadatas)
        
        # 4. 검색 테스트
        test_search(collection)
        
        print("\n" + "=" * 60)
        print("✅ 모든 처리가 완료되었습니다!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
