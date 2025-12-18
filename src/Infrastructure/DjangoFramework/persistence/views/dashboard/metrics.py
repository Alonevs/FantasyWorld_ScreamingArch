from collections import defaultdict

def group_items_by_author(items_list):
    """
    Groups a list of proposal items by their 'author' attribute.
    Returns a sorted list of dictionaries:
    [
        {'author': User, 'proposals': [sorted items], 'count': int},
        ...
    ]
    """
    grouped_map = defaultdict(list)
    for item in items_list:
        grouped_map[item.author].append(item)
    
    grouped_list = []
    for author, items in grouped_map.items():
        # Sort items inside group by created_at DESC
        items.sort(key=lambda x: x.created_at, reverse=True)
        
        grouped_list.append({
            'author': author,
            'proposals': items,
            'count': len(items)
        })
    
    # Sort groups by author username (handle None author)
    grouped_list.sort(key=lambda x: x['author'].username if x['author'] else "")
    
    return grouped_list

def calculate_kpis(pending_list, logs_list):
    """
    Calculates basic KPIs for the dashboard.
    """
    return {
        'total_pending_count': len(pending_list),
        'total_activity_count': len(logs_list)
    }
