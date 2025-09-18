import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from .utils import sanitize_subdomain, inject_tracking
from . import repository
from . import agents_repository as agents

bp = Blueprint('main', __name__)

TRACKING_TEMPLATE_HEAD = """<!-- Global Site Tag -->\n{global_site_tag}\n<!-- /Global Site Tag -->"""
TRACKING_TEMPLATE_BODY = """<!-- Tracking Codes -->\n<script>window.PHONE_TRACKING={phone_tracking!r};</script>\n<script>window.ZALO_TRACKING={zalo_tracking!r};</script>\n<script>window.FORM_TRACKING={form_tracking!r};</script>\n<!-- /Tracking Codes -->"""

@bp.route('/')
def index():
    filters = {
        'agent': request.args.get('agent','').strip(),
        'status': request.args.get('status','').strip(),
        'q': request.args.get('q','').strip(),
    }
    landings = repository.list_landings(filters)
    agents_list = agents.list_agents()
    return render_template('index.html', landings=landings, filters=filters, agents_list=agents_list)

@bp.route('/landing/<int:landing_id>')
def landing_detail(landing_id):
    landing = repository.get_landing(landing_id)
    if not landing:
        flash('Không tìm thấy landing page','danger')
        return redirect(url_for('main.index'))
    return render_template('detail.html', landing=landing)

@bp.route('/api/landingpages', methods=['GET'])
def api_list():
    filters = {
        'agent': request.args.get('agent','').strip(),
        'status': request.args.get('status','').strip(),
        'q': request.args.get('q','').strip(),
    }
    return jsonify(repository.list_landings(filters))

@bp.route('/api/landingpages', methods=['POST'])
def api_create():
    subdomain = sanitize_subdomain(request.form.get('subdomain',''))
    if not subdomain:
        return jsonify({'error':'Subdomain không hợp lệ'}), 400
    if repository.get_by_subdomain(subdomain):
        return jsonify({'error':'Subdomain đã tồn tại'}), 400

    agent = request.form.get('agent','').strip()
    global_site_tag = request.form.get('global_site_tag','').strip()
    phone_tracking = request.form.get('phone_tracking','').strip()
    zalo_tracking = request.form.get('zalo_tracking','').strip()
    form_tracking = request.form.get('form_tracking','').strip()
    hotline_phone = request.form.get('hotline_phone','').strip()
    zalo_phone = request.form.get('zalo_phone','').strip()
    google_form_link = request.form.get('google_form_link','').strip()

    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error':'Chưa chọn file index.html'}), 400
    filename = secure_filename(file.filename)
    html_content = file.read().decode('utf-8', errors='ignore')

    head_snippet = TRACKING_TEMPLATE_HEAD.format(global_site_tag=global_site_tag)
    body_snippet = TRACKING_TEMPLATE_BODY.format(phone_tracking=phone_tracking, zalo_tracking=zalo_tracking, form_tracking=form_tracking)
    final_html = inject_tracking(html_content, head_snippet, body_snippet)

    pub_root = current_app.config['PUBLISHED_ROOT']
    target_dir = os.path.join(pub_root, subdomain)
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, 'index.html')
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(final_html)

    landing_id = repository.create_landing({
        'subdomain': subdomain,
        'agent': agent,
        'global_site_tag': global_site_tag,
        'phone_tracking': phone_tracking,
        'zalo_tracking': zalo_tracking,
        'form_tracking': form_tracking,
        'hotline_phone': hotline_phone,
        'zalo_phone': zalo_phone,
        'google_form_link': google_form_link,
        'status': 'active',
        'original_filename': filename
    })

    return jsonify({'id': landing_id, 'message':'Tạo thành công'})

@bp.route('/api/landingpages/<int:landing_id>', methods=['PUT'])
def api_update(landing_id):
    landing = repository.get_landing(landing_id)
    if not landing:
        return jsonify({'error':'Không tồn tại'}), 404

    agent = request.form.get('agent', landing['agent']).strip()
    global_site_tag = request.form.get('global_site_tag', landing['global_site_tag'] or '').strip()
    phone_tracking = request.form.get('phone_tracking', landing['phone_tracking'] or '').strip()
    zalo_tracking = request.form.get('zalo_tracking', landing['zalo_tracking'] or '').strip()
    form_tracking = request.form.get('form_tracking', landing['form_tracking'] or '').strip()
    hotline_phone = request.form.get('hotline_phone', landing.get('hotline_phone') or '').strip()
    zalo_phone = request.form.get('zalo_phone', landing.get('zalo_phone') or '').strip()
    google_form_link = request.form.get('google_form_link', landing.get('google_form_link') or '').strip()

    file = request.files.get('file')
    if file and file.filename:
        filename = secure_filename(file.filename)
        html_content = file.read().decode('utf-8', errors='ignore')
    else:
        # Re-read current file from disk
        pub_root = current_app.config['PUBLISHED_ROOT']
        target_dir = os.path.join(pub_root, landing['subdomain'])
        with open(os.path.join(target_dir,'index.html'), 'r', encoding='utf-8') as f:
            html_content = f.read()
        filename = landing['original_filename']

    head_snippet = TRACKING_TEMPLATE_HEAD.format(global_site_tag=global_site_tag)
    body_snippet = TRACKING_TEMPLATE_BODY.format(phone_tracking=phone_tracking, zalo_tracking=zalo_tracking, form_tracking=form_tracking)
    final_html = inject_tracking(html_content, head_snippet, body_snippet)

    pub_root = current_app.config['PUBLISHED_ROOT']
    target_dir = os.path.join(pub_root, landing['subdomain'])
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, 'index.html')
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(final_html)

    repository.update_landing(landing_id, {
        'agent': agent,
        'global_site_tag': global_site_tag,
        'phone_tracking': phone_tracking,
        'zalo_tracking': zalo_tracking,
        'form_tracking': form_tracking,
        'hotline_phone': hotline_phone,
        'zalo_phone': zalo_phone,
        'google_form_link': google_form_link,
        'original_filename': filename
    })

    return jsonify({'message':'Cập nhật thành công'})

@bp.route('/api/landingpages/<int:landing_id>/status', methods=['PATCH'])
def api_change_status(landing_id):
    landing = repository.get_landing(landing_id)
    if not landing:
        return jsonify({'error':'Không tồn tại'}), 404
    new_status = request.json.get('status') if request.is_json else request.form.get('status')
    if new_status not in ('active','paused'):
        return jsonify({'error':'Trạng thái không hợp lệ'}), 400

    pub_root = current_app.config['PUBLISHED_ROOT']
    target_dir = os.path.join(pub_root, landing['subdomain'])
    index_file = os.path.join(target_dir, 'index.html')
    paused_file = os.path.join(target_dir, 'index.paused.html')

    if new_status == 'paused' and landing['status'] != 'paused':
        if os.path.exists(index_file):
            os.replace(index_file, paused_file)
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write('<html><head><meta charset="utf-8"><title>Tạm dừng</title></head><body><h3>Landing page đang tạm dừng.</h3></body></html>')
    elif new_status == 'active' and landing['status'] == 'paused':
        if os.path.exists(paused_file):
            if os.path.exists(index_file):
                os.remove(index_file)
            os.replace(paused_file, index_file)

    repository.update_landing(landing_id, {'status': new_status})
    return jsonify({'message':'Đổi trạng thái thành công'})

@bp.route('/api/landingpages/<int:landing_id>', methods=['DELETE'])
def api_delete(landing_id):
    landing = repository.get_landing(landing_id)
    if not landing:
        return jsonify({'error':'Không tồn tại'}), 404
    repository.delete_landing(landing_id)
    return jsonify({'message':'Đã xóa'})

# Basic HTML pages (reuse API via JS later if needed)
@bp.route('/create', methods=['GET'])
def create_page():
    return render_template('create.html', agents_list=agents.list_agents())

@bp.route('/edit/<int:landing_id>', methods=['GET'])
def edit_page(landing_id):
    landing = repository.get_landing(landing_id)
    if not landing:
        flash('Không tìm thấy','danger')
        return redirect(url_for('main.index'))
    return render_template('edit.html', landing=landing, agents_list=agents.list_agents())

# Serve published (dev helper only – in production Nginx will serve)
@bp.route('/_dev_published/<path:sub>/<path:filename>')
def dev_published(sub, filename):
    root = current_app.config['PUBLISHED_ROOT']
    return send_from_directory(os.path.join(root, sub), filename)

# ---------------- Agents UI & API -----------------
@bp.route('/agents')
def agents_page():
    agents_list = agents.list_agents()
    print(f"DEBUG: /agents route - Found {len(agents_list)} agents")
    for agent in agents_list:
        print(f"DEBUG: Agent {agent['id']}: {agent['name']} - {agent['phone']}")
    return render_template('agents.html', agents=agents_list)

@bp.route('/api/agents', methods=['GET'])
def api_agents_list():
    return jsonify(agents.list_agents())

@bp.route('/api/agents', methods=['POST'])
def api_agents_create():
    name = request.form.get('name','').strip()
    phone = request.form.get('phone','').strip()
    print(f"DEBUG: Creating agent - name: '{name}', phone: '{phone}'")
    if not name:
        print("DEBUG: Name is empty, returning error")
        return jsonify({'error':'Tên đại lý bắt buộc'}), 400
    agent_id = agents.create_agent(name, phone)
    print(f"DEBUG: Created agent with ID: {agent_id}")
    return jsonify({'id': agent_id, 'message':'Tạo thành công'})

@bp.route('/api/agents/<int:agent_id>', methods=['PUT'])
def api_agents_update(agent_id):
    a = agents.get_agent(agent_id)
    if not a:
        return jsonify({'error':'Không tồn tại'}), 404
    name = request.form.get('name','').strip()
    phone = request.form.get('phone','').strip()
    if not name:
        return jsonify({'error':'Tên đại lý bắt buộc'}), 400
    agents.update_agent(agent_id, name, phone)
    return jsonify({'message':'Cập nhật thành công'})

@bp.route('/api/agents/<int:agent_id>', methods=['DELETE'])
def api_agents_delete(agent_id):
    a = agents.get_agent(agent_id)
    if not a:
        return jsonify({'error':'Không tồn tại'}), 404
    agents.delete_agent(agent_id)
    return jsonify({'message':'Đã xóa'})
