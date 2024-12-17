import sys
import os

# 获取当前文件的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
root_dir = os.path.dirname(current_dir)
# 将项目根目录添加到 Python 路径
sys.path.append(root_dir)

from flask import Flask, jsonify, request
from flask_cors import CORS
from search import SearchEngine
from datetime import datetime
import logging
import json
from recommend.recommend import UserBasedRecommender
from auth import token_required, verify_user, generate_token, get_user_role

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 配置
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345678"
SEARCH_HISTORY_FILE = 'search_history.txt'

# 配置日志
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'server.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化搜索引擎
search_engine = SearchEngine(
    es_host='http://localhost:9201',
    index_name='nku_search'
)

recommender = UserBasedRecommender(
    es_host='http://localhost:9201',
    index_name='nku_search'
)

# 用户搜索历史
user_search_history = {}

@app.route('/api/search', methods=['GET'])
def search():
    """处理搜索请求"""
    try:
        # 获取查询参数
        query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        department = request.args.get('department')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by')
        sort_order = request.args.get('sort_order', 'desc')
        search_type = request.args.get('type', 'standard')  # 新增：搜索类型

        # 参数验证
        if page < 1:
            return jsonify({'error': '页码必须大于0'}), 400
        if size < 1 or size > 100:
            return jsonify({'error': '每页结果数必须在1-100之间'}), 400

        # 日期格式验证
        for date_str in [start_date, end_date]:
            if date_str:
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    return jsonify({'error': '日期格式无效，应为YYYY-MM-DD'}), 400

        # 根据搜索类型选择搜索方法
        if search_type == 'wildcard':
            results = search_engine.wildcard_search(query, page, size)
        elif search_type == 'phrase':
            results = search_engine.phrase_search(query, page, size)
        else:
            results = search_engine.basic_search(
                query=query,
                page=page,
                size=size,
                department=department,
                start_date=start_date,
                end_date=end_date,
                sort_by=sort_by,
                sort_order=sort_order
            )

        # 记录搜索日志
        log_data = {
            'query': query,
            'search_type': search_type,
            'department': department,
            'start_date': start_date,
            'end_date': end_date,
            'results_count': results.get('total', 0)
        }
        logger.info(f"搜索请求: {json.dumps(log_data, ensure_ascii=False)}")

        return jsonify(results)

    except Exception as e:
        logger.error(f"搜索请求处理出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """获取用户推荐"""
    try:
        # 获取用户ID
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': '需要用户ID'}), 400
            
        # 从搜索历史文件中获取用户历史
        history_data = {}
        if os.path.exists(SEARCH_HISTORY_FILE):
            with open(SEARCH_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        
        # 获取用户的搜索历史
        user_history = history_data.get(user_id, [])
        
        # 获取推荐
        recommendations = recommender.get_user_recommendations(
            user_id=user_id,
            search_history=user_history
        )
        
        return jsonify({
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"获取推荐时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

# 添加token验证接口
@app.route('/api/verify-token', methods=['GET'])
@token_required
def verify_token(current_user):
    """验证token"""
    return jsonify({
        'valid': True,
        'username': current_user,
        'role': get_user_role(current_user)
    })

# 替换原有的登录路由
@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if verify_user(username, password):
            token = generate_token(username)
            role = get_user_role(username)
            return jsonify({
                'token': token,
                'username': username,
                'role': role
            })
        else:
            return jsonify({'error': '用户名或密码错误'}), 401
            
    except Exception as e:
        logger.error(f"登录处理出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/search-history', methods=['GET'])
@token_required
def get_search_history(current_user):
    """获取用户搜索历史"""
    try:
        if os.path.exists(SEARCH_HISTORY_FILE):
            with open(SEARCH_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                user_history = history_data.get(current_user, [])
                return jsonify({'history': user_history})
        return jsonify({'history': []})
    except Exception as e:
        logger.error(f"获取搜索历史时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/search-history', methods=['POST'])
def store_search_history():
    """存储搜索历史"""
    try:
        data = request.get_json()
        username = data.get('username')
        search_text = data.get('search_text')

        if not username or not search_text:
            return jsonify({'error': '需要用户名和搜索内容'}), 400

        # 读取现有历史
        history_data = {}
        if os.path.exists(SEARCH_HISTORY_FILE):
            with open(SEARCH_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history_data = json.load(f)

        # 更新历史
        if username not in history_data:
            history_data[username] = []
        history_data[username].insert(0, {
            'text': search_text,
            'timestamp': datetime.now().isoformat()
        })
        # 限制历史记录数量
        history_data[username] = history_data[username][:100]

        # 保存历史
        with open(SEARCH_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)

        return jsonify({'message': '搜索历史已保存'})
    except Exception as e:
        logger.error(f"保存搜索历史时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/suggest', methods=['GET'])
def suggest():
    """处理搜索建议请求"""
    try:
        prefix = request.args.get('prefix', '')
        size = int(request.args.get('size', 5))

        if not prefix:
            return jsonify([])

        suggestions = search_engine.suggest_search(prefix, size)
        return jsonify(suggestions)

    except Exception as e:
        logger.error(f"获取搜索建议时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/departments', methods=['GET'])
def get_departments():
    """获取所有部门列表"""
    try:
        departments = search_engine.get_departments()
        return jsonify(departments)
    except Exception as e:
        logger.error(f"获取部门列表时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

def init_app():
    """应用初始化函数"""
    logger.info("服务器启动完成")
    return app

if __name__ == '__main__':
    app = init_app()
    app.run(host='127.0.0.1', port=5000, debug=True)