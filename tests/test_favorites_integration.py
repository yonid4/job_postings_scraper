"""
Test script to demonstrate the integration of favorites table into application models.

This script demonstrates:
1. Creating FavoriteListing instances
2. Adding favorites to the database
3. Retrieving user favorites
4. Checking if a job is favorited
5. Removing favorites
"""

import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend.src.data.supabase_manager import SupabaseManager, FavoriteListing

load_dotenv()


def test_favorites_integration():
    """Demonstrate the favorites functionality integration."""
    
    print("🧪 Testing Favorites Integration with Supabase")
    print("=" * 50)
    
    # Initialize Supabase manager
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in environment variables")
        return
    
    try:
        # Initialize the Supabase manager
        supabase_manager = SupabaseManager(supabase_url, supabase_key)
        print("✅ Supabase manager initialized successfully")
        
        # Test user and job IDs (you would normally get these from your application)
        test_user_id = str(uuid.uuid4())
        test_job_id = str(uuid.uuid4())
        
        print(f"\n📝 Test Data:")
        print(f"   User ID: {test_user_id}")
        print(f"   Job ID: {test_job_id}")
        
        # 1. Create a FavoriteListing instance
        print(f"\n1️⃣ Creating FavoriteListing instance...")
        favorite_data = FavoriteListing(
            user_id=test_user_id,
            job_id=test_job_id
        )
        print(f"✅ Created FavoriteListing: user_id={favorite_data.user_id}, job_id={favorite_data.job_id}")
        
        # 2. Add favorite to database
        print(f"\n2️⃣ Adding favorite to database...")
        try:
            created_favorite = supabase_manager.favorites.add_favorite(favorite_data)
            print(f"✅ Favorite added successfully!")
            print(f"   Favorite ID: {created_favorite.id}")
            print(f"   Created at: {created_favorite.created_at}")
        except Exception as e:
            print(f"❌ Failed to add favorite: {e}")
            return
        
        # 3. Check if job is favorited
        print(f"\n3️⃣ Checking if job is favorited...")
        is_favorited = supabase_manager.favorites.is_job_favorited(test_user_id, test_job_id)
        if is_favorited:
            print(f"✅ Job is favorited by user")
        else:
            print(f"❌ Job is not favorited by user")
        
        # 4. Get user favorites
        print(f"\n4️⃣ Retrieving user favorites...")
        user_favorites = supabase_manager.favorites.get_user_favorites(test_user_id)
        print(f"✅ Retrieved {len(user_favorites)} favorites for user")
        
        for i, favorite in enumerate(user_favorites, 1):
            print(f"   {i}. Job ID: {favorite.job_id}, Created: {favorite.created_at}")
        
        # 5. Get specific favorite by job
        print(f"\n5️⃣ Getting specific favorite by job...")
        specific_favorite = supabase_manager.favorites.get_favorite_by_job(test_user_id, test_job_id)
        if specific_favorite:
            print(f"✅ Found specific favorite: ID={specific_favorite.id}")
        else:
            print(f"❌ Specific favorite not found")
        
        # 6. Remove favorite by job
        print(f"\n6️⃣ Removing favorite by job...")
        removed = supabase_manager.favorites.remove_favorite_by_job(test_user_id, test_job_id)
        if removed:
            print(f"✅ Favorite removed successfully")
        else:
            print(f"❌ Failed to remove favorite")
        
        # 7. Verify removal
        print(f"\n7️⃣ Verifying removal...")
        is_favorited_after = supabase_manager.favorites.is_job_favorited(test_user_id, test_job_id)
        if not is_favorited_after:
            print(f"✅ Job is no longer favorited (removal confirmed)")
        else:
            print(f"❌ Job is still favorited (removal failed)")
        
        # 8. Test adding multiple favorites
        print(f"\n8️⃣ Testing multiple favorites...")
        job_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        for i, job_id in enumerate(job_ids, 1):
            try:
                new_favorite = FavoriteListing(user_id=test_user_id, job_id=job_id)
                created = supabase_manager.favorites.add_favorite(new_favorite)
                print(f"   ✅ Added favorite {i}: Job ID {job_id}")
            except Exception as e:
                print(f"   ❌ Failed to add favorite {i}: {e}")
        
        # 9. Get all favorites again
        print(f"\n9️⃣ Retrieving all favorites after multiple additions...")
        all_favorites = supabase_manager.favorites.get_user_favorites(test_user_id)
        print(f"✅ Total favorites for user: {len(all_favorites)}")
        
        # 10. Clean up - remove all test favorites
        print(f"\n🔟 Cleaning up test data...")
        removed_count = 0
        for favorite in all_favorites:
            if supabase_manager.favorites.remove_favorite(favorite.id):
                removed_count += 1
        
        print(f"✅ Removed {removed_count} test favorites")
        
        print(f"\n🎉 Favorites integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


def demonstrate_usage_examples():
    """Demonstrate usage examples for the favorites functionality."""
    
    print("\n" + "=" * 60)
    print("📚 USAGE EXAMPLES")
    print("=" * 60)
    
    print("""
# Example 1: Adding a job to favorites
favorite_data = FavoriteListing(
    user_id="user-uuid-here",
    job_id="job-uuid-here"
)
created_favorite = supabase_manager.favorites.add_favorite(favorite_data)
print(f"Added favorite with ID: {created_favorite.id}")

# Example 2: Checking if a job is favorited
is_favorited = supabase_manager.favorites.is_job_favorited("user-uuid", "job-uuid")
if is_favorited:
    print("This job is in your favorites!")

# Example 3: Getting all user favorites
user_favorites = supabase_manager.favorites.get_user_favorites("user-uuid")
for favorite in user_favorites:
    print(f"Favorited job: {favorite.job_id}")

# Example 4: Removing a favorite by job
removed = supabase_manager.favorites.remove_favorite_by_job("user-uuid", "job-uuid")
if removed:
    print("Favorite removed successfully")

# Example 5: Getting a specific favorite
specific_favorite = supabase_manager.favorites.get_favorite_by_job("user-uuid", "job-uuid")
if specific_favorite:
    print(f"Found favorite: {specific_favorite.id}")
""")


if __name__ == "__main__":
    test_favorites_integration()
    demonstrate_usage_examples() 