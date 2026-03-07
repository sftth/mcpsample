import chromadb
from chromadb.utils import embedding_functions

# 1. Persistent DB 연결
client = chromadb.PersistentClient(path="./chroma_store")

# 2. 임베딩 함수
sentence_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="agent_knowledge",
    embedding_function=sentence_ef
)

# ==========================
# 3. EC2 정보 분리 등록
# ==========================

documents = [
    "EC2 IP 정보: 15.168.235.199,56.155.82.169",
    "EC2 SSH User 정보: ec2-user",
    "EC2 PEM 경로: /home/ec2-user/.ssh/jacob.park-keypair.pem"
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

# 4. upsert (운영용 추천)
collection.upsert(
    ids=ids,
    documents=documents,
    metadatas=metadatas
)

print("✅ EC2 정보 3개 문서 분리 등록 완료")

# ==========================
# 5. 테스트 검색
# ==========================

result = collection.query(
    query_texts=["ec2 접속 pem 파일 위치는?"],
    n_results=3
)

print("\n🔎 검색 결과:")
print(result)