echo 'Initailzie environment...'
source .env;

echo "Create data path $DATA_STORAGE_PATH/$SCRAPED_DATA_PATH $DATA_STORAGE_PATH/$PROCESS_DATA_PATH ...";
mkdir -p "$DATA_STORAGE_PATH/$SCRAPED_DATA_PATH" "$DATA_STORAGE_PATH/$PROCESS_DATA_PATH";

echo "Create python virtual environment..."
python3 -m venv venv;
source ./venv/bin/activate;
echo "Installing python dependency..."
pip3 install -r ./requirements.txt
