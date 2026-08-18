SEARCH_PIPELINE = [
    {
        '$match': {
          'name': {'$eq': 'Kendall'}
        }
    }
]

SEARCH_FILTER_JOIN_PIPELINE = [
  {
    '$match': {
      'status': {'$eq': 'active'}
    }
  },
  {
    '$lookup': {
      'from': 'UserProfile',
      'localField': 'profile_id',
      'foreignField': '_id',
      'as': 'profile'
    }
  },
  {
    '$match': {
      'profile.country': {'$in': ['US', 'CA']}
    }
  },
  {
    '$sort': {
      'created_at': -1
    }
  },
  {
    '$limit': 10
  },
  {
    '$project': {
      'username': True,
      'email': True,
      'user_country': '$profile.country'
    }
  }
]


GROUPING_PIPELINE = [
  {
    '$match': {
      'status': { '$eq': 'completed' }
    }
  },
  {
    '$group': {
      '_id': '$category',
      'total_revenue': { '$sum': '$price' },
      'average_sale': { '$avg': '$price' },
      'total_items_sold': { '$count': {} }
    }
  }
]
