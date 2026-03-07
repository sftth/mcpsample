#!/usr/bin/env python3
"""
EC2 정보를 벡터DB에 등록하는 스크립트 (간소화 버전)

이미지 페이지 004에서 확인된 정보:
- Web1 IP: 13.208.128.117
- Web2 IP: 15.168.175.64
- Account: ec2-user
- PEM: /home/ec2-user/.ssh/jacob.park-keypair.pem
"""

import chromadb
from chromadb.utils import embedding_functions
import os


def register_to_vectordb():
    """EC2 정보를 벡터DB에 등록"""
    
    print("=" * 60)
    print("EC2 정보 → 벡터DB 등록 시작")
    print("=" * 60)
    
    # 1. EC2 정보 정의 (이미지에서 확인된 정보)
    print("\n[1단계] EC2 정보 준비...")
    
    # 이미지 페이지 004에서 확인된 EC2 정보
    ec2_ips = ["13.208.128.117", "15.168.175.64"]
    ec2_user = "ec2-user"
    ec2_pem = "/home/ec2-user/.ssh/jacob.park-keypair.pem"
    
    print(f"  IP 주소: {ec2_ips}")
    print(f"  SSH User: {ec2_user}")
    print(f"  PEM 경로: {ec2_pem}")
    
    # 2. ChromaDB 연결
    print("\n[2단계] ChromaDB 연결 중...")
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
    
    # 3. 기존 데이터 삭제
    print("\n[3단계] 기존 데이터 삭제 중...")
    try:
        # 모든 데이터 조회
        all_data = collection.get()
        if all_data and all_data.get('ids'):
            print(f"  삭제할 데이터: {len(all_data['ids'])}개")
            for doc_id in all_data['ids']:
                print(f"    - {doc_id}")
            collection.delete(ids=all_data['ids'])
            print("✅ 기존 데이터 삭제 완료")
        else:
            print("  삭제할 데이터 없음")
    except Exception as e:
        print(f"⚠️  데이터 삭제 중 오류: {e}")
    
    # 4. 새 데이터 등록
    print("\n[4단계] 벡터DB에 데이터 등록 중...")
    
    # 포맷에 맞춰 데이터 준비
    documents = [
        f"EC2 IP 정보: {','.join(ec2_ips)}",
        f"EC2 SSH User 정보: {ec2_user}",
        f"EC2 PEM 경로: {ec2_pem}"
    ]
    
    ids = [
        "ec2_ip_list",
        "ec2_ssh_user",
        "ec2_pem_path"
    ]
    
    metadatas = [
        {
            "type": "infrastructure",
            "service": "ec2",
            "field": "ip",
            "owner": "jacob.park"
        },
        {
            "type": "infrastructure",
            "service": "ec2",
            "field": "ssh_user",
            "owner": "jacob.park"
        },
        {
            "type": "infrastructure",
            "service": "ec2",
            "field": "pem_path",
            "owner": "jacob.park"
        }
    ]
    
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
    
    # 5. 검색 테스트
    print("\n[5단계] 검색 테스트...")
    try:
        test_queries = [
            "EC2 접속 정보를 알려줘",
            "EC2 IP 주소는?",
            "PEM 키 경로는?"
        ]
        
        for query in test_queries:
            print(f"\n🔎 질의: {query}")
            result = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if result and result.get('documents'):
                for docs in result['documents']:
                    for j, doc in enumerate(docs, 1):
                        print(f"  {j}. {doc}")
    except Exception as e:
        print(f"⚠️  검색 테스트 실패: {e}")
    
    print("\n" + "=" * 60)
    print("✅ EC2 정보 → 벡터DB 등록 완료!")
    print("=" * 60)


if __name__ == "__main__":
    register_to_vectordb()
