"""
Quick start script for Outbound Omega v2
"""
from app_main import create_app

if __name__ == '__main__':
    app = create_app('development')
    print("\n" + "="*60)
    print("🌌 Outbound Omega v2 - Starting...")
    print("="*60)
    print("\n📍 Server running at: http://localhost:5001")
    print("📖 Docs: See OUTBOUND_README.md\n")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=True)
