"""
UAT Manual Approval Interface
実際のユーザーによる手動承認インターフェース

Requirements: 全要件
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ManualApprovalInterface:
    """手動承認インターフェース"""
    
    def __init__(self, db_path: str = "data/uat_test.db"):
        self.db_path = db_path
        self.current_index = 0
        self.photos = []
    
    def load_pending_photos(self, test_run_id: str):
        """承認待ち写真を読み込み"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, photo_name, photo_path, ai_score, 
                   detected_context, selected_preset
            FROM uat_results
            WHERE test_run_id = ?
            AND processing_error IS NULL
            AND user_approved IS NULL
            ORDER BY ai_score DESC
        """, (test_run_id,))
        
        self.photos = cursor.fetchall()
        conn.close()
        
        return len(self.photos)
    
    def show_current_photo(self):
        """現在の写真情報を表示"""
        if self.current_index >= len(self.photos):
            return None
        
        photo = self.photos[self.current_index]
        photo_id, name, path, ai_score, context, preset = photo
        
        print("\n" + "="*60)
        print(f"Photo {self.current_index + 1}/{len(self.photos)}")
        print("="*60)
        print(f"Name: {name}")
        print(f"Path: {path}")
        print(f"AI Score: {ai_score:.2f}★")
        print(f"Context: {context}")
        print(f"Preset: {preset}")
        print("-"*60)
        
        return photo_id
    
    def get_user_approval(self, photo_id: int):
        """ユーザーから承認を取得"""
        while True:
            print("\nOptions:")
            print("  [a] Approve")
            print("  [r] Reject")
            print("  [s] Skip")
            print("  [q] Quit")
            
            choice = input("\nYour choice: ").lower().strip()
            
            if choice == 'a':
                rating = self._get_rating()
                feedback = input("Feedback (optional): ").strip()
                self._save_approval(photo_id, True, rating, feedback)
                return 'approved'
            elif choice == 'r':
                rating = self._get_rating()
                feedback = input("Reason for rejection: ").strip()
                self._save_approval(photo_id, False, rating, feedback)
                return 'rejected'
            elif choice == 's':
                return 'skipped'
            elif choice == 'q':
                return 'quit'
            else:
                print("Invalid choice. Please try again.")
    
    def _get_rating(self) -> int:
        """ユーザー評価を取得"""
        while True:
            try:
                rating = int(input("Rating (1-5): "))
                if 1 <= rating <= 5:
                    return rating
                print("Rating must be between 1 and 5")
            except ValueError:
                print("Please enter a number")
    
    def _save_approval(self, photo_id: int, approved: bool, 
                      rating: int, feedback: str):
        """承認データを保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE uat_results
            SET user_approved = ?,
                user_rating = ?,
                user_feedback = ?,
                approval_timestamp = ?
            WHERE id = ?
        """, (approved, rating, feedback, datetime.now(), photo_id))
        
        conn.commit()
        conn.close()
    
    def run_approval_session(self, test_run_id: str):
        """承認セッションを実行"""
        count = self.load_pending_photos(test_run_id)
        
        if count == 0:
            print("No pending photos for approval")
            return
        
        print(f"\nLoaded {count} photos for approval")
        
        approved = 0
        rejected = 0
        skipped = 0
        
        while self.current_index < len(self.photos):
            photo_id = self.show_current_photo()
            result = self.get_user_approval(photo_id)
            
            if result == 'approved':
                approved += 1
                self.current_index += 1
            elif result == 'rejected':
                rejected += 1
                self.current_index += 1
            elif result == 'skipped':
                skipped += 1
                self.current_index += 1
            elif result == 'quit':
                break
        
        print("\n" + "="*60)
        print("Approval Session Summary")
        print("="*60)
        print(f"Reviewed: {self.current_index}/{len(self.photos)}")
        print(f"Approved: {approved}")
        print(f"Rejected: {rejected}")
        print(f"Skipped: {skipped}")
        print(f"Approval Rate: {approved/(approved+rejected)*100:.1f}%" 
              if (approved+rejected) > 0 else "N/A")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UAT Manual Approval')
    parser.add_argument('test_run_id', type=str, 
                       help='Test run ID to approve')
    parser.add_argument('--db-path', type=str, default='data/uat_test.db',
                       help='Database path')
    
    args = parser.parse_args()
    
    interface = ManualApprovalInterface(args.db_path)
    interface.run_approval_session(args.test_run_id)


if __name__ == '__main__':
    main()
