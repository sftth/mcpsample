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

def format_as_spec(extracted_data: dict) -> list:
    """추출된 텍스트를 spec 포맷으로 변환"""
    print("\n📝 데이터 포맷 변환 중...")
    
    documents = []
    ids = []
    metadatas = []
    
    for idx, (filename, text) in enumerate(extracted_data.items(), 1):
        # 페이지 번호 추출
        page_num = filename.split('_page_')[-1].replace('.png', '')
        
        # 문서 ID 생성
        doc_id = f"requirement_page_{page_num}"
        
        # 문서 내용 (spec 포맷 스타일로)
        document = f"# 요구사항 정의서 - 페이지 {page_num}\n\n{text}"
        
        # 메타데이터
        metadata = {
            "type": "requirement",
            "source": "1650-01_요구사항정의서_v1.0",
            "page": page_num,
            "filename": filename
        }
        
        documents.append(document)
        ids.append(doc_id)
        metadatas.append(metadata)
        
        print(f"  ✓ {doc_id} 변환 완료")
    
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
        "요구사항은 무엇인가?",
        "시스템 구성은?",
        "기능 요구사항"
    ]
    
    for query in test_queries:
        print(f"\n  질문: {query}")
        result = collection.query(
            query_texts=[query],
            n_results=2
        )
        
        if result['documents'] and result['documents'][0]:
            for i, doc in enumerate(result['documents'][0], 1):
                print(f"    {i}. {doc[:100]}...")
                if result['metadatas'] and result['metadatas'][0]:
                    print(f"       메타데이터: {result['metadatas'][0][i-1]}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("이미지 → 텍스트 추출 → 벡터DB 등록 프로세스 시작")
    print("=" * 60)
    
    try:
        # 1. 이미지에서 텍스트 추출
        image_dir = "file/img"
        pattern = "1650-01_요구사항정의서_v1.0_page_*.png"
        extracted_data = extract_text_from_images(image_dir, pattern)
        
        # 2. spec 포맷으로 변환
        documents, ids, metadatas = format_as_spec(extracted_data)
        
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
