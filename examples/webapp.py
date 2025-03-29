#!/usr/bin/env python
"""
Example of using memfs in a web application
"""

import json
import time
import uuid
from datetime import datetime
from memfs import create_fs

try:
    # Try to import Flask
    from flask import Flask, request, jsonify, send_file, make_response
    import io

    HAS_FLASK = True
except ImportError:
    # If Flask is not installed, we'll simulate it for demonstration
    HAS_FLASK = False
    print("Flask not installed. Running in simulation mode.")


class MemfsWebDemo:
    """Web application demo using memfs as a storage backend."""

    def __init__(self):
        """Initialize the application with a virtual filesystem."""
        # Create a virtual filesystem
        self.fs = create_fs()

        # Create directory structure
        self.fs.makedirs('/uploads', exist_ok=True)
        self.fs.makedirs('/users', exist_ok=True)
        self.fs.makedirs('/content', exist_ok=True)

        # Initialize some demo data
        self._init_demo_data()

        if HAS_FLASK:
            # Create Flask application
            self.app = Flask(__name__)

            # Set up routes
            self.app.route('/api/users')(self.get_users)
            self.app.route('/api/users/<user_id>')(self.get_user)
            self.app.route('/api/content', methods=['GET'])(self.list_content)
            self.app.route('/api/content', methods=['POST'])(self.add_content)
            self.app.route('/api/content/<content_id>')(self.get_content)
            self.app.route('/api/content/<content_id>', methods=['DELETE'])(self.delete_content)
            self.app.route('/api/files/<path:file_path>')(self.get_file)
            self.app.route('/api/uploads', methods=['POST'])(self.upload_file)
            self.app.route('/api/status')(self.get_status)

    def _init_demo_data(self):
        """Initialize demo data in the virtual filesystem."""
        # Create some example users
        users = [
            {"id": "user1", "name": "Alice", "email": "alice@example.com"},
            {"id": "user2", "name": "Bob", "email": "bob@example.com"},
            {"id": "user3", "name": "Charlie", "email": "charlie@example.com"}
        ]

        for user in users:
            user_path = f"/users/{user['id']}.json"
            with self.fs.open(user_path, 'w') as f:
                json.dump(user, f)

        # Create some example content
        content_items = [
            {
                "id": "content1",
                "title": "Getting Started",
                "user_id": "user1",
                "created_at": "2023-01-01T12:00:00",
                "text": "This is a getting started guide."
            },
            {
                "id": "content2",
                "title": "Advanced Features",
                "user_id": "user2",
                "created_at": "2023-01-02T14:30:00",
                "text": "Learn about advanced features here."
            }
        ]

        for item in content_items:
            content_path = f"/content/{item['id']}.json"
            with self.fs.open(content_path, 'w') as f:
                json.dump(item, f)

        # Create a sample file
        self.fs.writefile('/uploads/sample.txt', 'This is a sample file for download.')

    def get_users(self):
        """API endpoint to get all users."""
        users = []

        for filename in self.fs.listdir('/users'):
            if filename.endswith('.json'):
                with self.fs.open(f'/users/{filename}', 'r') as f:
                    user = json.load(f)
                    users.append(user)

        return jsonify(users)

    def get_user(self, user_id):
        """API endpoint to get a specific user."""
        user_path = f'/users/{user_id}.json'

        if not self.fs.exists(user_path):
            return jsonify({"error": "User not found"}), 404

        with self.fs.open(user_path, 'r') as f:
            user = json.load(f)

        return jsonify(user)

    def list_content(self):
        """API endpoint to list all content items."""
        content_items = []

        for filename in self.fs.listdir('/content'):
            if filename.endswith('.json'):
                with self.fs.open(f'/content/{filename}', 'r') as f:
                    item = json.load(f)
                    content_items.append(item)

        return jsonify(content_items)

    def add_content(self):
        """API endpoint to add a new content item."""
        data = request.json

        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid data"}), 400

        if 'title' not in data or 'user_id' not in data:
            return jsonify({"error": "Missing required fields (title, user_id)"}), 400

        # Generate a new ID
        content_id = str(uuid.uuid4())[:8]

        # Create the content item
        content_item = {
            "id": content_id,
            "title": data['title'],
            "user_id": data['user_id'],
            "created_at": datetime.now().isoformat(),
            "text": data.get('text', '')
        }

        # Save to virtual filesystem
        content_path = f'/content/{content_id}.json'
        with self.fs.open(content_path, 'w') as f:
            json.dump(content_item, f)

        return jsonify(content_item), 201

    def get_content(self, content_id):
        """API endpoint to get a specific content item."""
        content_path = f'/content/{content_id}.json'

        if not self.fs.exists(content_path):
            return jsonify({"error": "Content not found"}), 404

        with self.fs.open(content_path, 'r') as f:
            content = json.load(f)

        return jsonify(content)

    def delete_content(self, content_id):
        """API endpoint to delete a content item."""
        content_path = f'/content/{content_id}.json'

        if not self.fs.exists(content_path):
            return jsonify({"error": "Content not found"}), 404

        # Remove the file
        self.fs.remove(content_path)

        return jsonify({"status": "deleted", "id": content_id})

    def get_file(self, file_path):
        """API endpoint to download a file."""
        full_path = f'/uploads/{file_path}'

        if not self.fs.exists(full_path):
            return jsonify({"error": "File not found"}), 404

        # Read the file from virtual filesystem
        file_content = self.fs.readfile(full_path)

        # Create a response with the file content
        if isinstance(file_content, str):
            # Text file
            response = make_response(file_content)
            response.headers['Content-Type'] = 'text/plain'
        else:
            # Binary file
            response = send_file(
                io.BytesIO(file_content),
                download_name=file_path.split('/')[-1],
                as_attachment=True
            )

        return response

    def upload_file(self):
        """API endpoint to upload a file."""
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Generate unique filename
        timestamp = int(time.time())
        filename = f"{timestamp}_{file.filename}"
        file_path = f'/uploads/{filename}'

        # Save file to virtual filesystem
        file_content = file.read()
        self.fs.writefilebytes(file_path, file_content)

        return jsonify({
            "status": "uploaded",
            "filename": filename,
            "size": len(file_content),
            "path": file_path
        }), 201

    def get_status(self):
        """API endpoint to get server status and filesystem info."""
        # Count items in the filesystem
        user_count = len([f for f in self.fs.listdir('/users') if f.endswith('.json')])
        content_count = len([f for f in self.fs.listdir('/content') if f.endswith('.json')])
        upload_count = len(self.fs.listdir('/uploads'))

        # Build directory structure
        structure = {}
        for root, dirs, files in self.fs.walk('/'):
            structure[root] = {
                "directories": dirs,
                "files": files
            }

        return jsonify({
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "users": user_count,
                "content": content_count,
                "uploads": upload_count
            },
            "filesystem": structure
        })

    def run(self, host='127.0.0.1', port=5000, debug=True):
        """Run the Flask application."""
        if HAS_FLASK:
            self.app.run(host=host, port=port, debug=debug)
        else:
            # If Flask is not installed, simulate the API for demonstration
            self._simulate_api()

    def _simulate_api(self):
        """Simulate API calls for demonstration purposes."""
        print("\n=== MEMFS Web Application Demo (Simulation) ===")
        print("(Flask not installed, running in simulation mode)")

        # Simulate GET /api/users
        print("\n1. GET /api/users")
        users = []
        for filename in self.fs.listdir('/users'):
            if filename.endswith('.json'):
                with self.fs.open(f'/users/{filename}', 'r') as f:
                    user = json.load(f)
                    users.append(user)
        print(f"Response: {json.dumps(users, indent=2)}")

        # Simulate GET /api/content
        print("\n2. GET /api/content")
        content_items = []
        for filename in self.fs.listdir('/content'):
            if filename.endswith('.json'):
                with self.fs.open(f'/content/{filename}', 'r') as f:
                    item = json.load(f)
                    content_items.append(item)
        print(f"Response: {json.dumps(content_items, indent=2)}")

        # Simulate POST /api/content
        print("\n3. POST /api/content")
        new_content = {
            "title": "New Article",
            "user_id": "user3",
            "text": "This is a new article created in the simulation."
        }
        print(f"Request: {json.dumps(new_content, indent=2)}")

        # Generate a new ID
        content_id = str(uuid.uuid4())[:8]

        # Create the content item
        content_item = {
            "id": content_id,
            "title": new_content['title'],
            "user_id": new_content['user_id'],
            "created_at": datetime.now().isoformat(),
            "text": new_content.get('text', '')
        }

        # Save to virtual filesystem
        content_path = f'/content/{content_id}.json'
        with self.fs.open(content_path, 'w') as f:
            json.dump(content_item, f)

        print(f"Response: {json.dumps(content_item, indent=2)}")

        # Simulate GET /api/status
        print("\n4. GET /api/status")
        # Count items in the filesystem
        user_count = len([f for f in self.fs.listdir('/users') if f.endswith('.json')])
        content_count = len([f for f in self.fs.listdir('/content') if f.endswith('.json')])
        upload_count = len(self.fs.listdir('/uploads'))

        status = {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "users": user_count,
                "content": content_count,
                "uploads": upload_count
            }
        }
        print(f"Response: {json.dumps(status, indent=2)}")

        print("\n=== End of Simulation ===")
        print("Install Flask to run the actual web application:\n  pip install flask")


def main():
    """Run the web application."""
    app = MemfsWebDemo()
    app.run()


if __name__ == "__main__":
    main()