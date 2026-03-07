#!/usr/bin/env python3
"""
이미지에서 EC2 정보를 추출하여 벡터DB에 등록하는 스크립트

입력:
- 산출물: img/1650-01_요구사항정의서_v1.0_page 형태의 모든 이미지 파일
- 벡터DB: chroma-agent
- 포맷: EC2 IP, SSH User, PEM 경로 정보

처리:
1. 이미지에서 OCR로 텍스트 추출
2. EC2 정보 파싱 (IP, SSH User, PEM 경로)
3. 벡터DB 기존 데이터 삭제
4. 포맷에 맞춰 벡터DB에 등록
"""

import chromadb
from chromadb.utils import embedding_functions
import os
import glob
from pathlib import Path

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("❌ 필요한 라이브러리가 설치되어 있지 않습니다.")
    print("설치 명령: pip install pillow pytesseract")
    exit(1)


def extract_text_from_image(image_path):
    """이미지에서 OCR로 텍스트 추출"""
    try:
        img = Image.open(image_path)
        # 한글 OCR 지원
        text = pytesseract.image_to_string(img, lang='kor+eng')
        return text
    except Exception as e:
        print(f"⚠️  이미지 텍스트 추출 실패 ({image_path}): {e}")
        return ""


def parse_ec2_info_from_text(text):
    """텍스트에서 EC2 정보 파싱"""
    ec2_info = {
        'ips': [],
        'ssh_user': None,
        'pem_path': None
    }
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # IP 주소 패턴 찾기 (xxx.xxx.xxx.xxx)
        import re
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, line)
        if ips:
            for ip in ips:
                # 유효한 IP인지 확인
                parts = ip.split('.')
                if all(0 <= int(p) <= 255 for p in parts):
                    if ip not in ec2_info['ips']:
                        ec2_info['ips'].append(ip)
        
        # SSH User 찾기 (ec2-user, Ec2-user 등)
        if 'ec2-user' in line.lower() or 'account' in line.lower():
            if 'ec2-user' in line.lower():
                ec2_info['ssh_user'] = 'ec2-user'
        
        # PEM 경로 찾기
        if '.pem' in line.lower() or 'keypair' in line.lower():
            # PEM 파일 경로 패턴
            pem_pattern = r'/[^\s]+\.pem|[^\s]+keypair\.pem'
            pem_matches = re.findall(pem_pattern, line)
            if pem_matches:
                ec2_info['pem_path'] = pem_matches[0]
            elif 'jacob' in line.lower() and 'park' in line.lower():
                # 기본 경로 추정
                ec2_info['pem_path'] = '/home/ec2-user/.ssh/jacob.park-keypair.pem'
    
    return ec2_info


def register_to_vectordb():
    """이미지에서 EC2 정보를 추출하여 벡터DB에 등록"""
    
    print("=" * 60)
    print("이미지 → 벡터DB 등록 시작")
    print("=" * 60)
    
    # 1. 이미지 파일 찾기
    print("\n[1단계] 이미지 파일 검색 중...")
    image_dir = "/home/ec2-user/mcpsample/file/img"
    image_pattern = os.path.join(image_dir, "1650-01_요구사항정의서_v1.0_page_*.png")
    image_files = sorted(glob.glob(image_pattern))
    
    if not image_files:
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_pattern}")
        return
    
    print(f"✅ {len(image_files)}개의 이미지 파일 발견")
    for img_file in image_files:
        print(f"   - {Path(img_file).name}")
    
    # 2. 이미지에서 텍스트 추출 및 EC2 정보 파싱
    print("\n[2단계] 이미지에서 EC2 정보 추출 중...")
    
    all_ec2_info = {
        'ips': set(),
        'ssh_user': None,
        'pem_path': None
    }
    
    for img_file in image_files:
        print(f"\n처리 중: {Path(img_file).name}")
        text = extract_text_from_image(img_file)
        
        if text:
            ec2_info = parse_ec2_info_from_text(text)
            
            # IP 주소 수집
            if ec2_info['ips']:
                print(f"  발견된 IP: {ec2_info['ips']}")
                all_ec2_info['ips'].update(ec2_info['ips'])
            
            # SSH User 수집
            if ec2_info['ssh_user']:
                print(f"  발견된 SSH User: {ec2_info['ssh_user']}")
                all_ec2_info['ssh_user'] = ec2_info['ssh_user']
            
            # PEM 경로 수집
            if ec2_info['pem_path']:
                print(f"  발견된 PEM 경로: {ec2_info['pem_path']}")
                all_ec2_info['pem_path'] = ec2_info['pem_path']
    
    # 수집된 정보 요약
    print("\n[추출된 EC2 정보 요약]")
    print(f"  IP 주소: {list(all_ec2_info['ips'])}")
    print(f"  SSH User: {all_ec2_info['ssh_user']}")
    print(f"  PEM 경로: {all_ec2_info['pem_path']}")
    
    if not all_ec2_info['ips'] and not all_ec2_info['ssh_user'] and not all_ec2_info['pem_path']:
        print("\n❌ EC2 정보를 추출할 수 없습니다.")
        return
    
    # 3. ChromaDB 연결
    print("\n[3단계] ChromaDB 연결 중...")
    chroma_path = "/home/ec2-user/mcpsample/chroma-agent/chroma_store"
    
    if not os.path.exists(chroma_path):
        print(f"❌ ChromaDB 경로가 존재하지 않습니다: {chroma_path}")
        return
    
    client = chromadb.PersistentClient(path=chroma_path)
    
    # 임베딩 함수 설정
    sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # 컬렉션 가져오기 또는 생성
    try:
        collection = client.get_or_create_collection(
            name="agent_knowledge",
            embedding_function=sentence_ef
        )
        print(f"✅ 컬렉션 'agent_knowledge' 연결 성공")
    except Exception as e:
        print(f"❌ 컬렉션 연결 실패: {e}")
        return
    
    # 4. 기존 데이터 삭제
    print("\n[4단계] 기존 데이터 삭제 중...")
    try:
        # 모든 데이터 조회
        all_data = collection.get()
        if all_data and all_data.get('ids'):
            print(f"  삭제할 데이터: {len(all_data['ids'])}개")
            collection.delete(ids=all_data['ids'])
            print("✅ 기존 데이터 삭제 완료")
        else:
            print("  삭제할 데이터 없음")
    except Exception as e:
        print(f"⚠️  데이터 삭제 중 오류: {e}")
    
    # 5. 새 데이터 등록
    print("\n[5단계] 벡터DB에 데이터 등록 중...")
    
    documents = []
    ids = []
    metadatas = []
    
    # IP 정보 등록
    if all_ec2_info['ips']:
        ip_list = ','.join(sorted(all_ec2_info['ips']))
        documents.append(f"EC2 IP 정보: {ip_list}")
        ids.append("ec2_ip_list")
        metadatas.append({
            "type": "infrastructure",
            "service": "ec2",
            "field": "ip",
            "owner": "jacob.park"
        })
    
    # SSH User 정보 등록
    if all_ec2_info['ssh_user']:
        documents.append(f"EC2 SSH User 정보: {all_ec2_info['ssh_user']}")
        ids.append("ec2_ssh_user")
        metadatas.append({
            "type": "infrastructure",
            "service": "ec2",
            "field": "ssh_user",
            "owner": "jacob.park"
        })
    
    # PEM 경로 정보 등록
    if all_ec2_info['pem_path']:
        documents.append(f"EC2 PEM 경로: {all_ec2_info['pem_path']}")
        ids.append("ec2_pem_path")
        metadatas.append({
            "type": "infrastructure",
            "service": "ec2",
            "field": "pem_path",
            "owner": "jacob.park"
        })
    
    if documents:
        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"✅ {len(documents)}개 문서 등록 완료")
            
            # 등록된 데이터 출력
            print("\n[등록된 데이터]")
            for i, (doc_id, document, metadata) in enumerate(zip(ids, documents, metadatas), 1):
                print(f"\n{i}. ID: {doc_id}")
                print(f"   문서: {document}")
                print(f"   메타데이터: {metadata}")
        except Exception as e:
            print(f"❌ 데이터 등록 실패: {e}")
            return
    else:
        print("❌ 등록할 데이터가 없습니다.")
        return
    
    # 6. 검색 테스트
    print("\n[6단계] 검색 테스트...")
    try:
        result = collection.query(
            query_texts=["EC2 접속 정보를 알려줘"],
            n_results=3
        )
        print("\n🔎 검색 결과:")
        if result and result.get('documents'):
            for i, docs in enumerate(result['documents']):
                for j, doc in enumerate(docs):
                    print(f"  {j+1}. {doc}")
    except Exception as e:
        print(f"⚠️  검색 테스트 실패: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 이미지 → 벡터DB 등록 완료!")
    print("=" * 60)


if __name__ == "__main__":
    register_to_vectordb()
