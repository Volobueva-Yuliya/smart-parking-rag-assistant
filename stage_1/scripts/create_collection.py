import weaviate
import weaviate.classes.config as wvc


def create_parking_collection():
    try:
        client = weaviate.connect_to_local()

        if client.collections.exists("ParkingKB"):
            client.collections.delete("ParkingKB")
            print("Deleted existing ParkingKB collection.")

        client.collections.create(
            name="ParkingKB",
            vector_config=wvc.Configure.Vectors.self_provided(),
            properties=[
                wvc.Property(name="content", data_type=wvc.DataType.TEXT),
                wvc.Property(name="section", data_type=wvc.DataType.TEXT),
                wvc.Property(name="source", data_type=wvc.DataType.TEXT),
                wvc.Property(name="chunk_id", data_type=wvc.DataType.TEXT),
            ],
        )

        print("Successfully created collection 'ParkingKB'.")
        client.close()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    create_parking_collection()