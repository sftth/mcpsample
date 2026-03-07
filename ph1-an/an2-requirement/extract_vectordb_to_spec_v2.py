#!/usr/bin/env python3
"""
벡터DB에서 데이터를 추출하여 spec-account.md 포맷으로 저장하는 스크립트

입력:
- 벡터DB: chroma-agent
- 포맷: ph3-im/mw/spec/spec-account.md
- 저장: ph1-an/an2-requirement/spec-account01.md

처리:
1. 벡터DB에서 모든 데이터 조회
2. spec-account.md 포맷으로 변환
3. spec-account01.md 파일로 저장
"""

import chromadb
from chromadb.utils import embedding_functions
import os


def extract_vectordb_to_spec():
    """벡터DB에서 데이터를 추출하여 spec 포맷으로 저장"""
    
    print("=" * 60)
    print("벡터DB → Spec 포맷 변환 시작")
    print("=" * 60)
    
    # 1. ChromaDB 연결
    print("\n[1단계] ChromaDB 연결 중...")
    chroma_path = "/home/ec2-user/mcpsample/chroma-agent/chroma_store"
    
    if not os.path.exists(chroma_path):
        print(f"❌ 오류: ChromaDB 경로가 존재하지 않습니다: {chroma_path}")
        return
    
    client = chromadb.PersistentClient(path=chroma_path)
    
    # 임베딩 함수 설정
    sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # 컬렉션 가져오기
    try:
        collection = client.get_collection(
            name="agent_knowledge",
            embedding_function=sentence_ef
        )
        print(f"✅ 컬렉션 'agent_knowledge' 연결 성공")
    except Exception as e:
        print(f"❌ 오류: 컬렉션을 가져올 수 없습니다: {e}")
        return
    
    # 2. 모든 데이터 조회
    print("\n[2단계] 벡터DB 데이터 조회 중...")
    try:
        # 컬렉션의 모든 데이터 가져오기
        all_data = collection.get()
        
        if not all_data or not all_data.get('ids'):
            print("❌ 벡터DB에 데이터가 없습니다.")
            return
        
        print(f"✅ 총 {len(all_data['ids'])}개의 문서 조회 완료")
        
        # 데이터 출력
        print("\n[조회된 데이터]")
        for i, (doc_id, document, metadata) in enumerate(zip(
            all_data['ids'], 
            all_data['documents'], 
            all_data['metadatas']
        ), 1):
            print(f"\n{i}. ID: {doc_id}")
            print(f"   문서: {document}")
            print(f"   메타데이터: {metadata}")
        
    except Exception as e:
        print(f"❌ 오류: 데이터 조회 실패: {e}")
        return
    
    # 3. Spec 포맷으로 변환
    print("\n[3단계] Spec 포맷으로 변환 중...")
    
    spec_content = generate_spec_format(all_data)
    
    # 4. 파일로 저장
    print("\n[4단계] 파일 저장 중...")
    output_path = "/home/ec2-user/mcpsample/ph1-an/an2-requirement/spec-account01.md"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        print(f"✅ 파일 저장 완료: {output_path}")
    except Exception as e:
        print(f"❌ 오류: 파일 저장 실패: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ 벡터DB → Spec 포맷 변환 완료!")
    print("=" * 60)


def generate_spec_format(data):
    """벡터DB 데이터를 spec-account.md 포맷으로 변환"""
    
    # spec-account.md 포맷 기반 템플릿
    spec_lines = []
    spec_lines.append("# EC2 계정 및 접속 정보")
    spec_lines.append("")
    
    # 데이터 분류
    ec2_info = {}
    
    for doc_id, document, metadata in zip(
        data['ids'], 
        data['documents'], 
        data['metadatas']
    ):
        if metadata and metadata.get('service') == 'ec2':
            field = metadata.get('field', 'unknown')
            ec2_info[field] = {
                'id': doc_id,
                'document': document,
                'metadata': metadata
            }
    
    # EC2 기본 정보
    spec_lines.append("## EC2 인스턴스 정보")
    spec_lines.append("")
    
    # IP 정보
    if 'ip' in ec2_info:
        ip_doc = ec2_info['ip']['document']
        # "EC2 IP 정보: 13.208.128.117,15.168.175.64" 형태에서 IP만 추출
        if ':' in ip_doc:
            ips = ip_doc.split(':')[1].strip()
            ip_list = [ip.strip() for ip in ips.split(',')]
            
            spec_lines.append("### 서버 목록")
            spec_lines.append("")
            for idx, ip in enumerate(ip_list, 1):
                spec_lines.append(f"#### Web{idx}")
                spec_lines.append(f"  - IP: {ip}")
                
                # SSH User 정보 추가
                if 'ssh_user' in ec2_info:
                    ssh_doc = ec2_info['ssh_user']['document']
                    if ':' in ssh_doc:
                        user = ssh_doc.split(':')[1].strip()
                        spec_lines.append(f"  - Account: {user}")
                
                # PEM 경로 추가
                if 'pem_path' in ec2_info:
                    pem_doc = ec2_info['pem_path']['document']
                    if ':' in pem_doc:
                        pem_path = pem_doc.split(':')[1].strip()
                        spec_lines.append(f"  - PEM: {pem_path}")
                
                spec_lines.append("")
    
    # 사전 준비 섹션
    spec_lines.append("## 사전 준비")
    spec_lines.append("")
    spec_lines.append("### SSH 접속 설정")
    spec_lines.append("")
    
    if 'pem_path' in ec2_info and 'ssh_user' in ec2_info and 'ip' in ec2_info:
        pem_path = ec2_info['pem_path']['document'].split(':')[1].strip()
        ssh_user = ec2_info['ssh_user']['document'].split(':')[1].strip()
        ips = ec2_info['ip']['document'].split(':')[1].strip()
        first_ip = ips.split(',')[0].strip()
        
        spec_lines.append("[예시]")
        spec_lines.append("  ```bash")
        spec_lines.append(f"  # PEM 키 권한 설정")
        spec_lines.append(f"  chmod 400 {pem_path}")
        spec_lines.append("")
        spec_lines.append(f"  # EC2 인스턴스 접속")
        spec_lines.append(f"  ssh -i {pem_path} {ssh_user}@{first_ip}")
        spec_lines.append("  ```")
        spec_lines.append("")
    
    # 접속 정보 요약
    spec_lines.append("## 접속 정보 요약")
    spec_lines.append("")
    
    if 'ssh_user' in ec2_info:
        ssh_user = ec2_info['ssh_user']['document'].split(':')[1].strip()
        spec_lines.append(f"  - User: {ssh_user}")
    
    if 'pem_path' in ec2_info:
        pem_path = ec2_info['pem_path']['document'].split(':')[1].strip()
        spec_lines.append(f"  - PEM 키: {pem_path}")
    
    if 'ip' in ec2_info:
        ips = ec2_info['ip']['document'].split(':')[1].strip()
        ip_list = [ip.strip() for ip in ips.split(',')]
        spec_lines.append(f"  - 서버 수: {len(ip_list)}대")
        spec_lines.append(f"  - IP 목록: {', '.join(ip_list)}")
    
    spec_lines.append("")
    
    # 메타데이터 정보
    spec_lines.append("## 메타데이터")
    spec_lines.append("")
    for field, info in ec2_info.items():
        metadata = info['metadata']
        spec_lines.append(f"### {field}")
        spec_lines.append(f"  - Type: {metadata.get('type', 'N/A')}")
        spec_lines.append(f"  - Service: {metadata.get('service', 'N/A')}")
        spec_lines.append(f"  - Owner: {metadata.get('owner', 'N/A')}")
        spec_lines.append("")
    
    return '\n'.join(spec_lines)


if __name__ == "__main__":
    extract_vectordb_to_spec()
