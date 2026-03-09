#!/usr/bin/env python3
"""
벡터DB에서 데이터를 추출하여 spec-account.md 포맷으로 저장하는 스크립트

입력:
- 벡터DB: chroma-agent
- 포맷: ph3-im/mw/spec/spec-account.md
- 저장: ph2-de/spec-account.md

처리:
1. 벡터DB에서 모든 데이터 조회
2. spec-account.md 포맷으로 변환
3. ph2-de/spec-account.md 파일로 저장
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
    
    # 4. 파일로 저장 (ph2-de 디렉토리로 변경)
    print("\n[4단계] 파일 저장 중...")
    output_path = "/home/ec2-user/mcpsample/ph2-de/spec-account.md"
    
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
    spec_lines.append("# EC2 인프라 정보")
    spec_lines.append("")
    spec_lines.append("## 문서 정보")
    spec_lines.append("벡터DB(chroma-agent)에서 추출한 EC2 인프라 정보입니다.")
    spec_lines.append("")
    
    # 인프라 정보 분류
    ec2_info = {
        'ip': [],
        'ssh_user': [],
        'pem_path': [],
        'other': []
    }
    
    for doc_id, document, metadata in zip(
        data['ids'], 
        data['documents'], 
        data['metadatas']
    ):
        if metadata and metadata.get('type') == 'infrastructure':
            field = metadata.get('field', 'other')
            if field in ec2_info:
                ec2_info[field].append({
                    'id': doc_id,
                    'document': document,
                    'metadata': metadata
                })
            else:
                ec2_info['other'].append({
                    'id': doc_id,
                    'document': document,
                    'metadata': metadata
                })
    
    # EC2 IP 정보
    if ec2_info['ip']:
        spec_lines.append("## EC2 IP 정보")
        spec_lines.append("")
        for item in ec2_info['ip']:
            spec_lines.append(f"  - {item['document']}")
            if item['metadata'].get('owner'):
                spec_lines.append(f"    - 담당자: {item['metadata']['owner']}")
        spec_lines.append("")
    
    # SSH User 정보
    if ec2_info['ssh_user']:
        spec_lines.append("## SSH 접속 정보")
        spec_lines.append("")
        for item in ec2_info['ssh_user']:
            spec_lines.append(f"  - {item['document']}")
        spec_lines.append("")
    
    # PEM 경로 정보
    if ec2_info['pem_path']:
        spec_lines.append("## PEM 키 경로")
        spec_lines.append("")
        for item in ec2_info['pem_path']:
            spec_lines.append(f"  - {item['document']}")
        spec_lines.append("")
    
    # 기타 정보
    if ec2_info['other']:
        spec_lines.append("## 기타 정보")
        spec_lines.append("")
        for item in ec2_info['other']:
            spec_lines.append(f"  - ID: {item['id']}")
            spec_lines.append(f"    - 내용: {item['document']}")
            spec_lines.append(f"    - 메타데이터: {item['metadata']}")
        spec_lines.append("")
    
    # 요약 정보
    spec_lines.append("## 요약")
    spec_lines.append("")
    total_docs = len(data['ids'])
    spec_lines.append(f"  - 총 문서 수: {total_docs}")
    spec_lines.append(f"  - IP 정보: {len(ec2_info['ip'])}개")
    spec_lines.append(f"  - SSH User 정보: {len(ec2_info['ssh_user'])}개")
    spec_lines.append(f"  - PEM 경로 정보: {len(ec2_info['pem_path'])}개")
    spec_lines.append(f"  - 기타 정보: {len(ec2_info['other'])}개")
    spec_lines.append("")
    
    # 상세 데이터 (참고용)
    spec_lines.append("## 상세 데이터 (참고)")
    spec_lines.append("")
    for i, (doc_id, document, metadata) in enumerate(zip(
        data['ids'], 
        data['documents'], 
        data['metadatas']
    ), 1):
        spec_lines.append(f"### {i}. {doc_id}")
        spec_lines.append("")
        spec_lines.append("**문서 내용:**")
        spec_lines.append(f"```")
        spec_lines.append(document)
        spec_lines.append(f"```")
        spec_lines.append("")
        spec_lines.append("**메타데이터:**")
        if metadata:
            for key, value in metadata.items():
                spec_lines.append(f"  - {key}: {value}")
        spec_lines.append("")
    
    return '\n'.join(spec_lines)


if __name__ == "__main__":
    extract_vectordb_to_spec()
