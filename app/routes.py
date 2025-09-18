
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import mimetypes
from .utils import sanitize_subdomain, inject_tracking
from . import repository
from . import agents_repository as agents
from .auth import User
from .forms import LoginForm, ChangePasswordForm

bp = Blueprint('main', __name__)

TRACKING_TEMPLATE_HEAD = """<!-- Global Site Tag -->\n{global_site_tag}\n<!-- /Global Site Tag -->"""
TRACKING_TEMPLATE_BODY = """<!-- Tracking Codes -->\n<script>window.PHONE_TRACKING={phone_tracking!r};</script>\n<script>window.ZALO_TRACKING={zalo_tracking!r};</script>\n<script>window.FORM_TRACKING={form_tracking!r};</script>\n<!-- /Tracking Codes -->"""

def save_uploaded_images(images, target_dir):
    """Save uploaded images with naming convention: anh1.jpg, anh2.png, etc. (max 7 images)"""
    if not images:
        return []
    
    # Limit to 7 images
    if len(images) > 7:
        raise ValueError('Tối đa 7 ảnh được phép upload')
    
    saved_files = []
    for i, image in enumerate(images, 1):
        if image.filename:
            # Get original file extension
            original_ext = os.path.splitext(secure_filename(image.filename))[1].lower()
            if not original_ext:
                original_ext = '.jpg'  # Default extension
            
            # Generate filename: anh1.jpg, anh2.png, etc.
            new_filename = f"anh{i}{original_ext}"
            filepath = os.path.join(target_dir, new_filename)
            
            try:
                image.save(filepath)
                saved_files.append(new_filename)
            except Exception as e:
                raise Exception(f'Lỗi lưu ảnh {new_filename}: {str(e)}')
    
    return saved_files

# Serve published landing pages - Simple approach
@bp.route('/landing/<subdomain>')
def serve_landing_simple(subdomain):
    """Serve published landing pages via /landing/<subdomain> URL"""
    pub_root = current_app.config['PUBLISHED_ROOT']
    landing_dir = os.path.join(pub_root, subdomain)
    index_file = os.path.join(landing_dir, 'index.html')
    
    # Check if landing page exists
    if not os.path.exists(index_file):
        return f"<h1>Landing page '{subdomain}' not found</h1><p>Please check if the landing page has been uploaded correctly.</p>", 404
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"<h1>Error loading landing page: {str(e)}</h1>", 500

# Serve static assets for landing pages
@bp.route('/landing/<subdomain>/<path:filename>')  
def serve_landing_assets_simple(subdomain, filename):
    """Serve static assets (images, etc.) for landing pages"""
    pub_root = current_app.config['PUBLISHED_ROOT']
    landing_dir = os.path.join(pub_root, subdomain)
    
    if not os.path.exists(os.path.join(landing_dir, filename)):
        return "File not found", 404
        
    return send_from_directory(landing_dir, filename)

# Company homepage (public)
@bp.route('/')
def company_home():
    return render_template('company_home.html')

# Login page
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/admin-panel-xyz123/')
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = '/admin-panel-xyz123/'
            flash('Đăng nhập thành công!', 'success')
            return redirect(next_page)
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'error')
    
    return render_template('login.html', form=form)

# Logout
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công', 'info')
    return redirect(url_for('main.company_home'))

# Admin dashboard (protected with secret URL)
@bp.route('/admin-panel-xyz123/')
@login_required
def admin_dashboard():
    filters = {
        'agent': request.args.get('agent','').strip(),
        'status': request.args.get('status','').strip(),
        'q': request.args.get('q','').strip(),
    }
    landings = repository.list_landings(filters)
    agents_list = agents.list_agents()
    return render_template('index.html', landings=landings, filters=filters, agents_list=agents_list)

# Admin agents page  
@bp.route('/admin-panel-xyz123/agents')
@login_required
def admin_agents():
    agents_list = agents.list_agents()
    return render_template('agents.html', agents=agents_list)

@bp.route('/landing/<int:landing_id>')
def landing_detail(landing_id):
    landing = repository.get_landing(landing_id)
    if not landing:
        flash('Không tìm thấy landing page','danger')
        return redirect(url_for('main.index'))
    return render_template('detail.html', landing=landing)

@bp.route('/api/landingpages', methods=['GET'])
@login_required
def api_list():
    filters = {
        'agent': request.args.get('agent','').strip(),
        'status': request.args.get('status','').strip(),
        'q': request.args.get('q','').strip(),
    }
    return jsonify(repository.list_landings(filters))

@bp.route('/api/landingpages', methods=['POST'])
@login_required
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

    # Process uploaded images
    images = request.files.getlist('images')
    
    head_snippet = TRACKING_TEMPLATE_HEAD.format(global_site_tag=global_site_tag)
    body_snippet = TRACKING_TEMPLATE_BODY.format(phone_tracking=phone_tracking, zalo_tracking=zalo_tracking, form_tracking=form_tracking)
    final_html = inject_tracking(html_content, head_snippet, body_snippet)

    pub_root = current_app.config['PUBLISHED_ROOT']
    target_dir = os.path.join(pub_root, subdomain)
    os.makedirs(target_dir, exist_ok=True)
    
    # Save HTML file
    target_file = os.path.join(target_dir, 'index.html')
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    # Save uploaded images
    try:
        saved_images = save_uploaded_images(images, target_dir)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

    return jsonify({
        'id': landing_id, 
        'message': f'Tạo thành công! Đã upload {len(saved_images)} ảnh: {", ".join(saved_images)}' if saved_images else 'Tạo thành công!',
        'images_uploaded': len(saved_images),
        'image_files': saved_images
    })

@bp.route('/api/landingpages/<int:landing_id>', methods=['PUT'])
@login_required
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

    # Process uploaded images if any
    pub_root = current_app.config['PUBLISHED_ROOT']
    target_dir = os.path.join(pub_root, landing['subdomain'])
    
    images = request.files.getlist('images')
    saved_images = []
    if images and any(img.filename for img in images):
        try:
            saved_images = save_uploaded_images(images, target_dir)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    head_snippet = TRACKING_TEMPLATE_HEAD.format(global_site_tag=global_site_tag)
    body_snippet = TRACKING_TEMPLATE_BODY.format(phone_tracking=phone_tracking, zalo_tracking=zalo_tracking, form_tracking=form_tracking)
    final_html = inject_tracking(html_content, head_snippet, body_snippet)

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

    result = {'message':'Cập nhật thành công'}
    if saved_images:
        result['images_uploaded'] = len(saved_images)
        result['image_files'] = saved_images
    
    return jsonify(result)

@bp.route('/api/landingpages/<int:landing_id>/status', methods=['PATCH'])
@login_required
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
@login_required
def api_delete(landing_id):
    landing = repository.get_landing(landing_id)
    if not landing:
        return jsonify({'error':'Không tồn tại'}), 404
    repository.delete_landing(landing_id)
    return jsonify({'message':'Đã xóa'})

# Basic HTML pages (reuse API via JS later if needed)
@bp.route('/admin-panel-xyz123/create', methods=['GET'])
@login_required
def create_page():
    return render_template('create.html', agents_list=agents.list_agents())

@bp.route('/admin-panel-xyz123/edit/<int:landing_id>', methods=['GET'])
@login_required  
def edit_page(landing_id):
    landing = repository.get_landing(landing_id)
    if not landing:
        flash('Không tìm thấy','danger')
        return redirect('/admin-panel-xyz123/')
    return render_template('edit.html', landing=landing, agents_list=agents.list_agents())

# Serve published (dev helper only – in production Nginx will serve)
@bp.route('/_dev_published/<path:sub>/<path:filename>')
def dev_published(sub, filename):
    root = current_app.config['PUBLISHED_ROOT']
    return send_from_directory(os.path.join(root, sub), filename)

# Serve assets for subdomains  
@bp.route('/_dev_published/<path:sub>/assets/<path:filename>')
def dev_published_assets(sub, filename):
    root = current_app.config['PUBLISHED_ROOT']
    assets_dir = os.path.join(root, sub, 'assets')
    return send_from_directory(assets_dir, filename)

# ---------------- Agents UI & API -----------------
@bp.route('/api/agents', methods=['GET'])
@login_required
def api_agents_list():
    return jsonify(agents.list_agents())

@bp.route('/api/agents', methods=['POST'])
@login_required
def api_agents_create():
    name = request.form.get('name','').strip()
    phone = request.form.get('phone','').strip()
    if not name:
        return jsonify({'error':'Tên đại lý bắt buộc'}), 400
    agent_id = agents.create_agent(name, phone)
    return jsonify({'id': agent_id, 'message':'Tạo thành công'})

@bp.route('/api/agents/<int:agent_id>', methods=['PUT'])
@login_required
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
@login_required
def api_agents_delete(agent_id):
    a = agents.get_agent(agent_id)
    if not a:
        return jsonify({'error':'Không tồn tại'}), 404
    agents.delete_agent(agent_id)
    return jsonify({'message':'Đã xóa'})
