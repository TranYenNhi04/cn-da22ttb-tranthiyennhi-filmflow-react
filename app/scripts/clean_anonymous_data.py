#!/usr/bin/env python3
"""
Script để xóa tất cả watch history và watchlist của Anonymous users
Chạy script này để dọn dẹp dữ liệu không mong muốn
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.db_postgresql import get_db_session
from data.models import WatchHistory, Watchlist, User

def clean_anonymous_data():
    """Xóa tất cả dữ liệu của Anonymous users"""
    with get_db_session() as db:
        # Count records before deletion
        watch_history_count = db.query(WatchHistory).filter(
            WatchHistory.user_id == 'Anonymous'
        ).count()
        
        watchlist_count = db.query(Watchlist).filter(
            Watchlist.user_id == 'Anonymous'
        ).count()
        
        print(f"\n🔍 Found:")
        print(f"   - {watch_history_count} watch history records for Anonymous")
        print(f"   - {watchlist_count} watchlist items for Anonymous")
        
        if watch_history_count == 0 and watchlist_count == 0:
            print("\n✅ No Anonymous data found. Database is clean!")
            return
        
        # Ask for confirmation
        response = input("\n⚠️  Do you want to delete all Anonymous data? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Cancelled.")
            return
        
        # Delete watch history
        deleted_history = db.query(WatchHistory).filter(
            WatchHistory.user_id == 'Anonymous'
        ).delete()
        
        # Delete watchlist
        deleted_watchlist = db.query(Watchlist).filter(
            Watchlist.user_id == 'Anonymous'
        ).delete()
        
        db.commit()
        
        print(f"\n✅ Deleted:")
        print(f"   - {deleted_history} watch history records")
        print(f"   - {deleted_watchlist} watchlist items")
        print("\n🎉 Database cleaned successfully!")

def show_anonymous_users():
    """Hiển thị tất cả users có tên Anonymous hoặc tương tự"""
    with get_db_session() as db:
        users = db.query(User).filter(
            User.user_id.ilike('%anonymous%')
        ).all()
        
        if not users:
            print("\n✅ No Anonymous users found in database.")
            return
        
        print(f"\n📋 Found {len(users)} Anonymous-like users:")
        for user in users:
            watch_count = db.query(WatchHistory).filter(
                WatchHistory.user_id == user.user_id
            ).count()
            watchlist_count = db.query(Watchlist).filter(
                Watchlist.user_id == user.user_id
            ).count()
            
            print(f"\n   User: {user.user_id}")
            print(f"   - Watch history: {watch_count} items")
            print(f"   - Watchlist: {watchlist_count} items")
            print(f"   - Created: {user.created_at}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧹 Clean Anonymous Data Script")
    print("=" * 60)
    
    try:
        # Show anonymous users first
        show_anonymous_users()
        
        # Clean anonymous data
        print("\n" + "-" * 60)
        clean_anonymous_data()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
