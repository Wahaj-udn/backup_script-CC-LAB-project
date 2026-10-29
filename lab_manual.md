# Lab Experiment: Cloud and Local Backup Utility

**AIM:** 
To demonstrate a backup strategy by writing and running a Python script that backs up files both locally and to the cloud (MongoDB), and to verify the successful restoration of these files.

**PROCEDURE:**

**Step 1: Prerequisites**
1. Create a free cluster on MongoDB Atlas.
2. Retrieve your connection string and ensure your IP address is added to the Network Access whitelist.
3. Open your terminal, create a virtual environment, and install the required libraries:
   `pip install pymongo python-dotenv certifi`

**Step 2: Configuration**
1. Create a file named `.env` in the project root directory.
2. Add your MongoDB connection string into the `.env` file:
   `MONGO_URI=mongodb+srv://<username>:<password>@<your_cluster_address>`

**Step 3: Write the Backup Script**
1. Create a file named `backup.py`.
2. Write the Python code that:
   - Uses `shutil` to copy files to a local timestamped folder.
   - Uses `gridfs` and `pymongo` to upload those same files to the MongoDB Atlas cluster.
   - Uses `hashlib` to compute a SHA-256 checksum for each file to ensure data integrity.
   - Implements a command-line interface with `backup`, `restore-local`, and `restore-cloud` options.

**Step 4: Prepare the Data**
1. Create a folder named `important_files` in the project directory.
2. Add a few sample files (like a text document or an image) inside the `important_files` folder to serve as the data you want to protect.

**Step 5: Perform the Backup**
1. Run the backup command in your terminal:
   `python backup.py backup`
2. **Local check:** Verify that a new folder with the current timestamp was created inside the `backup/` directory on your computer.
3. **Cloud check:** Open your MongoDB Atlas dashboard and check the `backup_demo` database to see the newly uploaded files.

**Step 6: Test the Recovery**
1. Simulate data loss by manually deleting the files inside the `important_files` folder.
2. Test the local restore command:
   `python backup.py restore-local`
3. Confirm the files have been recovered successfully.
4. Delete the files again to test the cloud functionality.
5. Test the cloud restore command:
   `python backup.py restore-cloud`
6. Verify that the files were correctly downloaded from the cloud and restored.

**CONCLUSION:**
The experiment successfully demonstrates automated data backup, verifying that lost files can be fully recovered from both local and cloud storage sources.
