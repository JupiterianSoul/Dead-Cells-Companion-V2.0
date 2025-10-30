from flask import Flask, render_template, jsonify, request, send_file
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global data storage
items_data = []
notes_file = 'data/item_notes.json'
items_file = 'items.json'

def load_items():
    """Load items from JSON file"""
    global items_data
    try:
        with open(items_file, 'r', encoding='utf-8') as f:
            items_data = json.load(f)
        return True
    except Exception as e:
        print(f"Error loading items: {e}")
        return False

def load_notes():
    """Load user notes from JSON file"""
    try:
        if os.path.exists(notes_file):
            with open(notes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading notes: {e}")
    return {}

def save_notes(notes):
    """Save user notes to JSON file"""
    try:
        os.makedirs('data', exist_ok=True)
        with open(notes_file, 'w', encoding='utf-8') as f:
            json.dump(notes, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving notes: {e}")
        return False

def get_item_category(item):
    """Extract category from item type"""
    item_type = item.get('infobox', {}).get('type', '')
    if 'Melee' in item_type:
        return 'melee'
    elif 'Ranged' in item_type:
        return 'ranged'
    elif 'Shield' in item_type:
        return 'shield'
    elif 'Grenade' in item_type:
        return 'grenade'
    elif 'Deployable' in item_type:
        return 'deployable'
    elif 'Power' in item_type:
        return 'power'
    return 'other'

def parse_numeric(value_str):
    """Extract first numeric value from string"""
    if not value_str:
        return 0
    import re
    match = re.search(r'[\d.]+', str(value_str))
    return float(match.group()) if match else 0

# Initialize data on startup
load_items()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/items')
def get_items():
    """Get all items with optional filtering and sorting"""
    # Get query parameters
    search = request.args.get('search', '').lower()
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    # Filter items
    filtered = items_data
    
    # Category filter
    if category != 'all':
        filtered = [item for item in filtered if get_item_category(item) == category]
    
    # Search filter
    if search:
        filtered = [
            item for item in filtered
            if search in item.get('name', '').lower() or
               search in item.get('long_description', '').lower() or
               search in json.dumps(item.get('infobox', {})).lower()
        ]
    
    # Sort items
    if sort_by == 'name':
        filtered.sort(key=lambda x: x.get('name', '').lower())
    elif sort_by == 'dps':
        filtered.sort(key=lambda x: parse_numeric(x.get('infobox', {}).get('base_dps', 0)))
    elif sort_by == 'price':
        filtered.sort(key=lambda x: parse_numeric(x.get('infobox', {}).get('money_cost', 0)))
    
    if order == 'desc':
        filtered.reverse()
    
    # Paginate
    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = filtered[start:end]
    
    return jsonify({
        'items': paginated,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/api/categories')
def get_categories():
    """Get all unique categories"""
    categories = set()
    for item in items_data:
        categories.add(get_item_category(item))
    return jsonify(['all'] + sorted(list(categories)))

@app.route('/api/item/<path:item_name>')
def get_item(item_name):
    """Get specific item by name"""
    for item in items_data:
        if item.get('name') == item_name:
            return jsonify(item)
    return jsonify({'error': 'Item not found'}), 404

@app.route('/api/random')
def get_random():
    """Get a random item"""
    import random
    if items_data:
        return jsonify(random.choice(items_data))
    return jsonify({'error': 'No items available'}), 404

@app.route('/api/notes', methods=['GET', 'POST'])
def handle_notes():
    """Get or save notes"""
    if request.method == 'GET':
        return jsonify(load_notes())
    
    elif request.method == 'POST':
        notes = request.json
        if save_notes(notes):
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to save notes'}), 500

@app.route('/api/export/<format>')
def export_data(format):
    """Export data in JSON or CSV format"""
    search = request.args.get('search', '')
    category = request.args.get('category', 'all')
    
    # Get filtered items
    filtered = items_data
    if category != 'all':
        filtered = [item for item in filtered if get_item_category(item) == category]
    if search:
        search = search.lower()
        filtered = [
            item for item in filtered
            if search in item.get('name', '').lower()
        ]
    
    if format == 'json':
        filename = f'deadcells_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, indent=2)
        return send_file(filename, as_attachment=True, download_name=filename)
    
    elif format == 'csv':
        import csv
        filename = f'deadcells_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Type', 'Base DPS', 'Price', 'Unlock Cost', 'URL'])
            
            for item in filtered:
                infobox = item.get('infobox', {})
                writer.writerow([
                    item.get('name', ''),
                    infobox.get('type', ''),
                    infobox.get('base_dps', ''),
                    infobox.get('money_cost', ''),
                    infobox.get('blueprint_cost', ''),
                    item.get('url', '')
                ])
        
        return send_file(filename, as_attachment=True, download_name=filename)
    
    return jsonify({'error': 'Invalid format'}), 400

@app.route('/api/reload')
def reload_items():
    """Reload items from JSON file"""
    if load_items():
        return jsonify({'success': True, 'count': len(items_data)})
    return jsonify({'error': 'Failed to reload items'}), 500

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    categories = {}
    for item in items_data:
        cat = get_item_category(item)
        categories[cat] = categories.get(cat, 0) + 1
    
    return jsonify({
        'total_items': len(items_data),
        'categories': categories,
        'last_updated': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
