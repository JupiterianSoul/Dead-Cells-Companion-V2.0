import unittest
import json
import os
from app import app, load_items, get_item_category, parse_numeric

class TestDeadCellsDB(unittest.TestCase):
    
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True
        load_items()
    
    def test_home_page(self):
        """Test main page loads"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_get_items(self):
        """Test getting all items"""
        response = self.app.get('/api/items')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('items', data)
        self.assertIn('total', data)
        self.assertGreater(data['total'], 0)
    
    def test_search_filter(self):
        """Test search filtering"""
        response = self.app.get('/api/items?search=bow')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        # All items should contain 'bow' in name or description
        for item in data['items']:
            self.assertTrue(
                'bow' in item['name'].lower() or 
                'bow' in item.get('long_description', '').lower()
            )
    
    def test_category_filter(self):
        """Test category filtering"""
        response = self.app.get('/api/items?category=melee')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        for item in data['items']:
            self.assertEqual(get_item_category(item), 'melee')
    
    def test_sorting(self):
        """Test sorting functionality"""
        response = self.app.get('/api/items?sort=name&order=asc')
        data = json.loads(response.data)
        items = data['items']
        if len(items) > 1:
            # Check if sorted alphabetically
            for i in range(len(items) - 1):
                self.assertLessEqual(
                    items[i]['name'].lower(), 
                    items[i+1]['name'].lower()
                )
    
    def test_pagination(self):
        """Test pagination"""
        response1 = self.app.get('/api/items?page=1&per_page=10')
        response2 = self.app.get('/api/items?page=2&per_page=10')
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        self.assertEqual(len(data1['items']), 10)
        # Items on different pages should be different
        self.assertNotEqual(data1['items'][0]['name'], data2['items'][0]['name'])
    
    def test_get_specific_item(self):
        """Test getting a specific item"""
        # Get first item from list
        response = self.app.get('/api/items?per_page=1')
        data = json.loads(response.data)
        item_name = data['items'][0]['name']
        
        # Get that specific item
        response = self.app.get(f'/api/item/{item_name}')
        self.assertEqual(response.status_code, 200)
        item_data = json.loads(response.data)
        self.assertEqual(item_data['name'], item_name)
    
    def test_get_nonexistent_item(self):
        """Test getting an item that doesn't exist"""
        response = self.app.get('/api/item/NonexistentItem123')
        self.assertEqual(response.status_code, 404)
    
    def test_get_random_item(self):
        """Test random item endpoint"""
        response = self.app.get('/api/random')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('name', data)
    
    def test_get_categories(self):
        """Test categories endpoint"""
        response = self.app.get('/api/categories')
        self.assertEqual(response.status_code, 200)
        categories = json.loads(response.data)
        self.assertIsInstance(categories, list)
        self.assertIn('all', categories)
    
    def test_notes_endpoints(self):
        """Test notes save and load"""
        test_notes = {'Test Item': 'Test note content'}
        
        # Save notes
        response = self.app.post('/api/notes',
                                data=json.dumps(test_notes),
                                content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Load notes
        response = self.app.get('/api/notes')
        self.assertEqual(response.status_code, 200)
        notes = json.loads(response.data)
        self.assertEqual(notes.get('Test Item'), 'Test note content')
    
    def test_get_stats(self):
        """Test stats endpoint"""
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_items', data)
        self.assertIn('categories', data)
    
    def test_get_item_category(self):
        """Test category extraction"""
        melee_item = {'infobox': {'type': 'TypeMelee Weapon'}}
        ranged_item = {'infobox': {'type': 'TypeRanged Weapon'}}
        shield_item = {'infobox': {'type': 'TypeShield'}}
        
        self.assertEqual(get_item_category(melee_item), 'melee')
        self.assertEqual(get_item_category(ranged_item), 'ranged')
        self.assertEqual(get_item_category(shield_item), 'shield')
    
    def test_parse_numeric(self):
        """Test numeric parsing from strings"""
        self.assertEqual(parse_numeric('Base DPS113'), 113.0)
        self.assertEqual(parse_numeric('2000'), 2000.0)
        self.assertEqual(parse_numeric('1.5 seconds'), 1.5)
        self.assertEqual(parse_numeric('No numbers'), 0)
        self.assertEqual(parse_numeric(None), 0)

if __name__ == '__main__':
    unittest.main()
