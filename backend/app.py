import os
from datetime import datetime, date, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, Material, Project, MaterialUsage, ProcessPhoto, Order, Task
from sqlalchemy import func, and_

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///craft.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/materials', methods=['GET'])
def get_materials():
    search = request.args.get('search', '')
    material_type = request.args.get('type', '')
    
    query = Material.query
    if search:
        query = query.filter(Material.name.contains(search) | Material.color_code.contains(search))
    if material_type:
        query = query.filter(Material.material_type == material_type)
    
    materials = query.order_by(Material.created_at.desc()).all()
    return jsonify([m.to_dict() for m in materials])


@app.route('/api/materials/<int:id>', methods=['GET'])
def get_material(id):
    material = Material.query.get_or_404(id)
    return jsonify(material.to_dict())


@app.route('/api/materials', methods=['POST'])
def create_material():
    data = request.form.to_dict()
    file = request.files.get('photo')
    
    filename = None
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"material_{datetime.utcnow().timestamp()}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    material = Material(
        name=data['name'],
        material_type=data['material_type'],
        color_code=data.get('color_code'),
        width=float(data['width']),
        total_length=float(data['total_length']),
        remaining_length=float(data['total_length']),
        unit_price=float(data['unit_price']),
        supplier=data.get('supplier'),
        purchase_date=date.fromisoformat(data['purchase_date']),
        photo=filename,
        notes=data.get('notes')
    )
    db.session.add(material)
    db.session.commit()
    return jsonify(material.to_dict()), 201


@app.route('/api/materials/<int:id>', methods=['PUT'])
def update_material(id):
    material = Material.query.get_or_404(id)
    data = request.form.to_dict()
    file = request.files.get('photo')
    
    if file and allowed_file(file.filename):
        if material.photo:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], material.photo)
            if os.path.exists(old_path):
                os.remove(old_path)
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"material_{datetime.utcnow().timestamp()}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        material.photo = filename
    
    if 'name' in data:
        material.name = data['name']
    if 'material_type' in data:
        material.material_type = data['material_type']
    if 'color_code' in data:
        material.color_code = data['color_code']
    if 'width' in data:
        material.width = float(data['width'])
    if 'total_length' in data:
        new_total = float(data['total_length'])
        used_total = material.used_length_total
        
        if new_total < used_total:
            return jsonify({
                'error': f'材料总长度不能低于已被作品占用的长度 {used_total:.2f} 米。当前已被 {len(material.usages)} 个作品使用。'
            }), 400
        
        old_total = material.total_length
        diff = new_total - old_total
        material.total_length = new_total
        material.remaining_length += diff
        
        if material.remaining_length < 0:
            material.remaining_length = 0
    if 'unit_price' in data:
        material.unit_price = float(data['unit_price'])
    if 'supplier' in data:
        material.supplier = data['supplier']
    if 'purchase_date' in data:
        material.purchase_date = date.fromisoformat(data['purchase_date'])
    if 'notes' in data:
        material.notes = data['notes']
    
    db.session.commit()
    return jsonify(material.to_dict())


@app.route('/api/materials/<int:id>', methods=['DELETE'])
def delete_material(id):
    material = Material.query.get_or_404(id)
    
    if material.is_used:
        project_names = [p['project_name'] for p in material.used_by_projects]
        return jsonify({
            'error': f'该材料已被作品使用，无法直接删除。请先在以下作品中移除用料：{", ".join(project_names)}',
            'used_by_projects': material.used_by_projects
        }), 400
    
    if material.photo:
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], material.photo)
        if os.path.exists(old_path):
            os.remove(old_path)
    db.session.delete(material)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@app.route('/api/projects', methods=['GET'])
def get_projects():
    status = request.args.get('status', '')
    project_type = request.args.get('type', '')
    
    query = Project.query
    if status:
        query = query.filter(Project.status == status)
    if project_type:
        query = query.filter(Project.project_type == project_type)
    
    projects = query.order_by(Project.created_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


@app.route('/api/projects/<int:id>', methods=['GET'])
def get_project(id):
    project = Project.query.get_or_404(id)
    data = project.to_dict()
    data['material_usages'] = [u.to_dict() for u in project.material_usages]
    data['process_photos'] = [p.to_dict() for p in sorted(project.process_photos, key=lambda x: x.stage_order)]
    return jsonify(data)


@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    
    target_quantity = int(data.get('target_quantity', 1))
    completed_quantity = int(data.get('completed_quantity', 0))
    
    if completed_quantity > target_quantity:
        return jsonify({
            'error': f'已完成数量 ({completed_quantity}) 不能超过目标数量 ({target_quantity})'
        }), 400
    
    project = Project(
        name=data['name'],
        project_type=data['project_type'],
        description=data.get('description'),
        start_date=date.fromisoformat(data['start_date']),
        end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None,
        status=data.get('status', 'in_progress'),
        target_quantity=target_quantity,
        completed_quantity=completed_quantity,
        notes=data.get('notes')
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@app.route('/api/projects/<int:id>', methods=['PUT'])
def update_project(id):
    project = Project.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        project.name = data['name']
    if 'project_type' in data:
        project.project_type = data['project_type']
    if 'description' in data:
        project.description = data['description']
    if 'start_date' in data:
        project.start_date = date.fromisoformat(data['start_date'])
    if 'end_date' in data:
        project.end_date = date.fromisoformat(data['end_date']) if data['end_date'] else None
    if 'status' in data:
        project.status = data['status']
    
    target_quantity = project.target_quantity
    completed_quantity = project.completed_quantity
    
    if 'target_quantity' in data:
        target_quantity = int(data['target_quantity'])
    if 'completed_quantity' in data:
        completed_quantity = int(data['completed_quantity'])
    
    if completed_quantity > target_quantity:
        return jsonify({
            'error': f'已完成数量 ({completed_quantity}) 不能超过目标数量 ({target_quantity})'
        }), 400
    
    project.target_quantity = target_quantity
    project.completed_quantity = completed_quantity
    
    if 'notes' in data:
        project.notes = data['notes']
    
    db.session.commit()
    return jsonify(project.to_dict())


@app.route('/api/projects/<int:id>', methods=['DELETE'])
def delete_project(id):
    project = Project.query.get_or_404(id)
    for photo in project.process_photos:
        if photo.photo:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo)
            if os.path.exists(old_path):
                os.remove(old_path)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@app.route('/api/projects/<int:id>/materials', methods=['POST'])
def add_project_material(id):
    project = Project.query.get_or_404(id)
    data = request.get_json()
    material = Material.query.get_or_404(data['material_id'])
    
    used_length = float(data['used_length'])
    cutting_loss = float(data.get('cutting_loss', 0))
    total_needed = used_length + cutting_loss
    
    if material.remaining_length < total_needed:
        return jsonify({'error': f'材料剩余不足，仅剩 {material.remaining_length} 米'}), 400
    
    usage = MaterialUsage(
        project_id=id,
        material_id=data['material_id'],
        used_length=used_length,
        cutting_loss=cutting_loss,
        notes=data.get('notes')
    )
    
    material.remaining_length -= total_needed
    db.session.add(usage)
    db.session.commit()
    return jsonify(usage.to_dict()), 201


@app.route('/api/material-usages/<int:id>', methods=['DELETE'])
def delete_material_usage(id):
    usage = MaterialUsage.query.get_or_404(id)
    material = usage.material
    material.remaining_length += usage.used_length + usage.cutting_loss
    db.session.delete(usage)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@app.route('/api/projects/<int:id>/photos', methods=['POST'])
def add_project_photo(id):
    project = Project.query.get_or_404(id)
    data = request.form.to_dict()
    file = request.files.get('photo')
    
    if not file or not allowed_file(file.filename):
        return jsonify({'error': '请上传有效的图片文件'}), 400
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"process_{datetime.utcnow().timestamp()}.{ext}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    photo = ProcessPhoto(
        project_id=id,
        stage=data['stage'],
        stage_order=int(data.get('stage_order', 0)),
        photo=filename,
        description=data.get('description'),
        experience=data.get('experience')
    )
    db.session.add(photo)
    db.session.commit()
    return jsonify(photo.to_dict()), 201


@app.route('/api/process-photos/<int:id>', methods=['PUT'])
def update_process_photo(id):
    photo = ProcessPhoto.query.get_or_404(id)
    data = request.get_json()
    
    if 'stage' in data:
        photo.stage = data['stage']
    if 'stage_order' in data:
        photo.stage_order = int(data['stage_order'])
    if 'description' in data:
        photo.description = data['description']
    if 'experience' in data:
        photo.experience = data['experience']
    
    db.session.commit()
    return jsonify(photo.to_dict())


@app.route('/api/process-photos/<int:id>', methods=['DELETE'])
def delete_process_photo(id):
    photo = ProcessPhoto.query.get_or_404(id)
    if photo.photo:
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.photo)
        if os.path.exists(old_path):
            os.remove(old_path)
    db.session.delete(photo)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@app.route('/api/process-photos', methods=['GET'])
def get_all_process_photos():
    project_id = request.args.get('project_id')
    query = ProcessPhoto.query
    if project_id:
        query = query.filter(ProcessPhoto.project_id == int(project_id))
    photos = query.order_by(ProcessPhoto.created_at.desc()).all()
    result = []
    for p in photos:
        d = p.to_dict()
        d['project_name'] = p.project.name if p.project else None
        result.append(d)
    return jsonify(result)


@app.route('/api/statistics/overview', methods=['GET'])
def get_overview_stats():
    total_materials = Material.query.count()
    total_projects = Project.query.count()
    completed_projects = Project.query.filter_by(status='completed').count()
    total_material_value = db.session.query(func.sum(Material.remaining_length * Material.unit_price)).scalar() or 0
    
    total_material_cost = 0
    total_utilization = 0
    usage_count = 0
    usages = MaterialUsage.query.all()
    for u in usages:
        total_material_cost += u.total_cost
        total_utilization += u.utilization_rate
        usage_count += 1
    
    avg_utilization = total_utilization / usage_count if usage_count > 0 else 0
    
    return jsonify({
        'total_materials': total_materials,
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'total_material_value': round(total_material_value, 2),
        'total_material_cost': round(total_material_cost, 2),
        'avg_utilization': round(avg_utilization * 100, 2)
    })


@app.route('/api/statistics/material-consumption', methods=['GET'])
def get_material_consumption():
    thirty_days_ago = date.today()
    results = db.session.query(
        Material.material_type,
        func.sum(MaterialUsage.used_length + MaterialUsage.cutting_loss).label('total_used')
    ).select_from(MaterialUsage).join(
        Material, MaterialUsage.material_id == Material.id
    ).filter(
        MaterialUsage.created_at >= datetime.utcnow().replace(day=1)
    ).group_by(Material.material_type).all()
    
    labels = []
    data = []
    for r in results:
        labels.append(r[0])
        data.append(round(r[1], 2))
    
    return jsonify({'labels': labels, 'data': data})


@app.route('/api/statistics/utilization', methods=['GET'])
def get_utilization_stats():
    results = db.session.query(
        Material.material_type,
        func.avg(MaterialUsage.used_length / (MaterialUsage.used_length + MaterialUsage.cutting_loss))
    ).select_from(MaterialUsage).join(
        Material, MaterialUsage.material_id == Material.id
    ).group_by(Material.material_type).all()
    
    labels = []
    data = []
    for r in results:
        if r[1] is not None:
            labels.append(r[0])
            data.append(round(r[1] * 100, 2))
    
    return jsonify({'labels': labels, 'data': data})


@app.route('/api/statistics/project-types', methods=['GET'])
def get_project_types():
    results = db.session.query(
        Project.project_type,
        func.count(Project.id)
    ).group_by(Project.project_type).all()
    
    labels = []
    data = []
    for r in results:
        labels.append(r[0])
        data.append(r[1])
    
    return jsonify({'labels': labels, 'data': data})


@app.route('/api/statistics/idle-materials', methods=['GET'])
def get_idle_materials():
    days_threshold = int(request.args.get('days', 90))
    min_remaining = float(request.args.get('min_remaining', 1))
    
    today = date.today()
    idle_materials = []
    
    materials = Material.query.filter(
        Material.remaining_length >= min_remaining
    ).all()
    
    for m in materials:
        last_usage = MaterialUsage.query.filter_by(
            material_id=m.id
        ).order_by(MaterialUsage.created_at.desc()).first()
        
        if last_usage:
            days_idle = (today - last_usage.created_at.date()).days
        else:
            days_idle = (today - m.purchase_date).days
        
        if days_idle >= days_threshold:
            d = m.to_dict()
            d['days_idle'] = days_idle
            d['last_used'] = last_usage.created_at.date().isoformat() if last_usage else None
            idle_materials.append(d)
    
    idle_materials.sort(key=lambda x: x['days_idle'], reverse=True)
    return jsonify(idle_materials)


@app.route('/api/statistics/cost-trend', methods=['GET'])
def get_cost_trend():
    months = []
    costs = []
    
    for i in range(5, -1, -1):
        month_date = date.today().replace(day=1)
        if month_date.month - i <= 0:
            month = month_date.month - i + 12
            year = month_date.year - 1
        else:
            month = month_date.month - i
            year = month_date.year
        
        start_dt = datetime(year, month, 1)
        if month == 12:
            end_dt = datetime(year + 1, 1, 1)
        else:
            end_dt = datetime(year, month + 1, 1)
        
        total = 0
        usages = MaterialUsage.query.filter(
            and_(
                MaterialUsage.created_at >= start_dt,
                MaterialUsage.created_at < end_dt
            )
        ).all()
        
        for u in usages:
            if u.material:
                total += (u.used_length + u.cutting_loss) * u.material.unit_price
        
        months.append(f"{year}年{month}月")
        costs.append(round(total, 2))
    
    return jsonify({'months': months, 'costs': costs})


@app.route('/api/statistics/anomalies', methods=['GET'])
def get_anomalies():
    anomalies = {
        'insufficient_stock': [],
        'over_target': [],
        'material_conflicts': [],
        'negative_inventory': [],
        'over_usage_rate': [],
        'overdue_orders': [],
        'high_risk_orders': []
    }
    
    materials = Material.query.all()
    for m in materials:
        if m.remaining_length <= 0:
            anomalies['insufficient_stock'].append({
                'type': 'insufficient_stock',
                'material_id': m.id,
                'material_name': m.name,
                'remaining_length': m.remaining_length,
                'total_length': m.total_length,
                'message': f'材料"{m.name}"库存已用尽'
            })
        elif m.remaining_length < 1:
            anomalies['insufficient_stock'].append({
                'type': 'insufficient_stock',
                'material_id': m.id,
                'material_name': m.name,
                'remaining_length': m.remaining_length,
                'total_length': m.total_length,
                'message': f'材料"{m.name}"库存不足，仅剩 {m.remaining_length:.2f} 米'
            })
        
        if m.remaining_length < 0:
            anomalies['negative_inventory'].append({
                'type': 'negative_inventory',
                'material_id': m.id,
                'material_name': m.name,
                'remaining_length': m.remaining_length,
                'total_value': m.remaining_length * m.unit_price,
                'message': f'材料"{m.name}"出现负库存: {m.remaining_length:.2f} 米'
            })
        
        usage_rate = 1 - (m.remaining_length / m.total_length) if m.total_length > 0 else 0
        if usage_rate > 1:
            anomalies['over_usage_rate'].append({
                'type': 'over_usage_rate',
                'material_id': m.id,
                'material_name': m.name,
                'usage_rate': usage_rate * 100,
                'message': f'材料"{m.name}"使用率超过 100%: {(usage_rate * 100):.1f}%'
            })
        
        if m.total_length < m.used_length_total:
            anomalies['material_conflicts'].append({
                'type': 'material_conflict',
                'material_id': m.id,
                'material_name': m.name,
                'total_length': m.total_length,
                'used_length_total': m.used_length_total,
                'used_by_projects': m.used_by_projects,
                'message': f'材料"{m.name}"总长度 ({m.total_length:.2f}m) 小于已使用长度 ({m.used_length_total:.2f}m)'
            })
    
    projects = Project.query.all()
    for p in projects:
        if p.completed_quantity > p.target_quantity:
            anomalies['over_target'].append({
                'type': 'over_target',
                'project_id': p.id,
                'project_name': p.name,
                'completed_quantity': p.completed_quantity,
                'target_quantity': p.target_quantity,
                'message': f'作品"{p.name}"完成数量 ({p.completed_quantity}) 超过目标数量 ({p.target_quantity})'
            })
    
    total_count = (len(anomalies['insufficient_stock']) + 
                   len(anomalies['over_target']) + 
                   len(anomalies['material_conflicts']) + 
                   len(anomalies['negative_inventory']) + 
                   len(anomalies['over_usage_rate']))
    
    orders = Order.query.all()
    for o in orders:
        if o.is_overdue:
            anomalies['overdue_orders'].append({
                'type': 'overdue_order',
                'order_id': o.id,
                'customer_name': o.customer_name,
                'project_name': o.project_name,
                'days_overdue': -o.days_until_delivery if o.days_until_delivery else 0,
                'message': f'订单"{o.customer_name}"已逾期 {(-o.days_until_delivery) if o.days_until_delivery else 0} 天'
            })
        elif o.delivery_risk == 'high':
            anomalies['high_risk_orders'].append({
                'type': 'high_risk_order',
                'order_id': o.id,
                'customer_name': o.customer_name,
                'project_name': o.project_name,
                'days_until_delivery': o.days_until_delivery,
                'message': f'订单"{o.customer_name}"交付风险高，仅剩 {o.days_until_delivery} 天'
            })
    
    total_count = (len(anomalies['insufficient_stock']) + 
                   len(anomalies['over_target']) + 
                   len(anomalies['material_conflicts']) + 
                   len(anomalies['negative_inventory']) + 
                   len(anomalies['over_usage_rate']) +
                   len(anomalies.get('overdue_orders', [])) +
                   len(anomalies.get('high_risk_orders', [])))
    
    summary = {
        'insufficient_stock': len(anomalies['insufficient_stock']),
        'over_target': len(anomalies['over_target']),
        'material_conflicts': len(anomalies['material_conflicts']),
        'negative_inventory': len(anomalies['negative_inventory']),
        'over_usage_rate': len(anomalies['over_usage_rate']),
        'overdue_orders': len(anomalies.get('overdue_orders', [])),
        'high_risk_orders': len(anomalies.get('high_risk_orders', []))
    }
    
    return jsonify({
        'total_count': total_count,
        'anomalies': anomalies,
        'summary': summary
    })


@app.route('/api/orders', methods=['GET'])
def get_orders():
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Order.query
    if status:
        query = query.filter(Order.status == status)
    if search:
        query = query.filter(Order.customer_name.contains(search) | Order.requirement.contains(search))
    
    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders])


@app.route('/api/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    data = order.to_dict()
    if order.project:
        data['material_usages'] = [u.to_dict() for u in order.project.material_usages]
        data['process_photos'] = [p.to_dict() for p in sorted(order.project.process_photos, key=lambda x: x.stage_order)]
    return jsonify(data)


@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    
    project_id = None
    if data.get('create_new_project') and data.get('project_name'):
        project_data = {
            'name': data['project_name'],
            'project_type': data.get('project_type', '其他'),
            'description': data.get('requirement', ''),
            'start_date': date.today().isoformat(),
            'target_quantity': data.get('target_quantity', 1),
            'completed_quantity': 0,
            'status': 'in_progress' if data.get('status') in ['in_progress', 'confirmed'] else 'in_progress'
        }
        project = Project(
            name=project_data['name'],
            project_type=project_data['project_type'],
            description=project_data['description'],
            start_date=date.fromisoformat(project_data['start_date']),
            target_quantity=project_data['target_quantity'],
            completed_quantity=project_data['completed_quantity'],
            status=project_data['status']
        )
        db.session.add(project)
        db.session.flush()
        project_id = project.id
    elif data.get('project_id'):
        project_id = data.get('project_id')
    
    order = Order(
        customer_name=data['customer_name'],
        contact_info=data['contact_info'],
        order_source=data.get('order_source'),
        requirement=data.get('requirement'),
        delivery_date=date.fromisoformat(data['delivery_date']) if data.get('delivery_date') else None,
        quoted_price=float(data.get('quoted_price', 0)),
        deposit=float(data.get('deposit', 0)),
        balance=float(data.get('balance', 0)),
        status=data.get('status', 'pending'),
        notes=data.get('notes'),
        project_id=project_id
    )
    
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201


@app.route('/api/orders/<int:id>', methods=['PUT'])
def update_order(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()
    
    old_status = order.status
    
    if 'customer_name' in data:
        order.customer_name = data['customer_name']
    if 'contact_info' in data:
        order.contact_info = data['contact_info']
    if 'order_source' in data:
        order.order_source = data['order_source']
    if 'requirement' in data:
        order.requirement = data['requirement']
    if 'delivery_date' in data:
        order.delivery_date = date.fromisoformat(data['delivery_date']) if data['delivery_date'] else None
    if 'quoted_price' in data:
        order.quoted_price = float(data['quoted_price'])
    if 'deposit' in data:
        order.deposit = float(data['deposit'])
    if 'balance' in data:
        order.balance = float(data['balance'])
    if 'notes' in data:
        order.notes = data['notes']
    
    if 'project_id' in data or data.get('create_new_project'):
        if data.get('create_new_project') and data.get('project_name'):
            project_data = {
                'name': data['project_name'],
                'project_type': data.get('project_type', '其他'),
                'description': data.get('requirement', order.requirement or ''),
                'start_date': date.today().isoformat(),
                'target_quantity': data.get('target_quantity', 1),
                'completed_quantity': 0,
                'status': 'in_progress'
            }
            project = Project(
                name=project_data['name'],
                project_type=project_data['project_type'],
                description=project_data['description'],
                start_date=date.fromisoformat(project_data['start_date']),
                target_quantity=project_data['target_quantity'],
                completed_quantity=project_data['completed_quantity'],
                status=project_data['status']
            )
            db.session.add(project)
            db.session.flush()
            order.project_id = project.id
        else:
            order.project_id = data.get('project_id') or None
    
    if 'status' in data and data['status'] != old_status:
        order.status = data['status']
        
        if order.project:
            if data['status'] in ['in_progress', 'confirmed']:
                order.project.status = 'in_progress'
            elif data['status'] == 'ready':
                order.project.status = 'in_progress'
            elif data['status'] == 'completed':
                order.project.status = 'completed'
                if order.project.completed_quantity == 0:
                    order.project.completed_quantity = order.project.target_quantity
            elif data['status'] == 'cancelled':
                order.project.status = 'paused'
    
    db.session.commit()
    return jsonify(order.to_dict())


@app.route('/api/orders/<int:id>', methods=['DELETE'])
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@app.route('/api/orders/<int:id>/suggested-price', methods=['GET'])
def get_suggested_price(id):
    order = Order.query.get_or_404(id)
    return jsonify({
        'material_cost': order.material_cost,
        'suggested_price': order.suggested_price,
        'profit_estimate': order.suggested_price - order.material_cost,
        'profit_margin': round(((order.suggested_price - order.material_cost) / order.suggested_price * 100), 2) if order.suggested_price > 0 else 0
    })


@app.route('/api/statistics/order-overview', methods=['GET'])
def get_order_overview():
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    in_progress_orders = Order.query.filter_by(status='in_progress').count()
    ready_orders = Order.query.filter_by(status='ready').count()
    completed_orders = Order.query.filter_by(status='completed').count()
    
    overdue_orders = Order.query.filter(
        Order.status.notin_(['completed', 'cancelled']),
        Order.delivery_date.isnot(None)
    ).all()
    overdue_count = sum(1 for o in overdue_orders if o.is_overdue)
    
    total_revenue = db.session.query(func.sum(Order.quoted_price)).filter(
        Order.status == 'completed'
    ).scalar() or 0
    
    total_material_cost = 0
    total_profit = 0
    completed_order_list = Order.query.filter_by(status='completed').all()
    for o in completed_order_list:
        cost = o.material_cost
        total_material_cost += cost
        total_profit += (o.quoted_price - cost)
    
    profit_rate = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    high_risk_count = sum(1 for o in Order.query.filter(
        Order.status.notin_(['completed', 'cancelled'])
    ).all() if o.delivery_risk == 'high')
    
    return jsonify({
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'ready_orders': ready_orders,
        'completed_orders': completed_orders,
        'overdue_orders': overdue_count,
        'high_risk_orders': high_risk_count,
        'total_revenue': round(total_revenue, 2),
        'total_material_cost': round(total_material_cost, 2),
        'total_profit': round(total_profit, 2),
        'profit_rate': round(profit_rate, 2),
        'pending_delivery': ready_orders
    })


@app.route('/api/statistics/order-trend', methods=['GET'])
def get_order_trend():
    months = []
    revenues = []
    order_counts = []
    
    for i in range(5, -1, -1):
        month_date = date.today().replace(day=1)
        if month_date.month - i <= 0:
            month = month_date.month - i + 12
            year = month_date.year - 1
        else:
            month = month_date.month - i
            year = month_date.year
        
        start_dt = datetime(year, month, 1)
        if month == 12:
            end_dt = datetime(year + 1, 1, 1)
        else:
            end_dt = datetime(year, month + 1, 1)
        
        orders = Order.query.filter(
            and_(
                Order.created_at >= start_dt,
                Order.created_at < end_dt
            )
        ).all()
        
        revenue = sum(o.quoted_price for o in orders if o.status == 'completed')
        
        months.append(f"{year}年{month}月")
        revenues.append(round(revenue, 2))
        order_counts.append(len(orders))
    
    return jsonify({
        'months': months,
        'revenues': revenues,
        'order_counts': order_counts
    })


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    assignee = request.args.get('assignee', '')
    project_id = request.args.get('project_id', '')
    order_id = request.args.get('order_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = Task.query
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee:
        query = query.filter(Task.assignee.contains(assignee))
    if project_id:
        query = query.filter(Task.project_id == int(project_id))
    if order_id:
        query = query.filter(Task.order_id == int(order_id))
    if start_date:
        query = query.filter(Task.estimated_start_date >= date.fromisoformat(start_date))
    if end_date:
        query = query.filter(Task.estimated_end_date <= date.fromisoformat(end_date))
    
    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks])


@app.route('/api/tasks/calendar', methods=['GET'])
def get_tasks_calendar():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    query = Task.query
    if start_date:
        query = query.filter(Task.estimated_end_date >= date.fromisoformat(start_date))
    if end_date:
        query = query.filter(Task.estimated_start_date <= date.fromisoformat(end_date))
    
    tasks = query.order_by(Task.estimated_start_date).all()
    
    events = []
    for t in tasks:
        color = '#e91e63'
        if t.status == 'completed':
            color = '#4caf50'
        elif t.status == 'in_progress':
            color = '#2196f3'
        elif t.status == 'delayed':
            color = '#f44336'
        elif t.priority == 'high':
            color = '#ff9800'
        
        events.append({
            'id': t.id,
            'title': t.name,
            'start': t.estimated_start_date.isoformat() if t.estimated_start_date else None,
            'end': t.estimated_end_date.isoformat() if t.estimated_end_date else None,
            'status': t.status,
            'priority': t.priority,
            'assignee': t.assignee,
            'project_id': t.project_id,
            'project_name': t.project_name,
            'order_id': t.order_id,
            'order_customer': t.order_customer,
            'progress': t.progress,
            'color': color,
            'extendedProps': t.to_dict()
        })
    
    return jsonify(events)


@app.route('/api/tasks/<int:id>', methods=['GET'])
def get_task(id):
    task = Task.query.get_or_404(id)
    return jsonify(task.to_dict())


@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': '任务名称不能为空'}), 400
    if not data.get('stage'):
        return jsonify({'error': '制作阶段不能为空'}), 400
    
    task = Task(
        name=data['name'],
        project_id=data.get('project_id'),
        order_id=data.get('order_id'),
        stage=data['stage'],
        estimated_start_date=date.fromisoformat(data['estimated_start_date']) if data.get('estimated_start_date') else None,
        estimated_end_date=date.fromisoformat(data['estimated_end_date']) if data.get('estimated_end_date') else None,
        estimated_hours=float(data.get('estimated_hours', 0)),
        actual_hours=float(data.get('actual_hours', 0)),
        assignee=data.get('assignee'),
        priority=data.get('priority', 'medium'),
        status=data.get('status', 'pending'),
        notes=data.get('notes')
    )
    
    db.session.add(task)
    db.session.flush()
    
    if task.order_id and not task.project_id:
        order = Order.query.get(task.order_id)
        if order and order.project_id:
            task.project_id = order.project_id
    
    db.session.commit()
    return jsonify(task.to_dict()), 201


@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    task = Task.query.get_or_404(id)
    data = request.get_json()
    
    old_status = task.status
    
    if 'name' in data:
        task.name = data['name']
    if 'project_id' in data:
        task.project_id = data.get('project_id') or None
    if 'order_id' in data:
        task.order_id = data.get('order_id') or None
    if 'stage' in data:
        task.stage = data['stage']
    if 'estimated_start_date' in data:
        task.estimated_start_date = date.fromisoformat(data['estimated_start_date']) if data['estimated_start_date'] else None
    if 'estimated_end_date' in data:
        task.estimated_end_date = date.fromisoformat(data['estimated_end_date']) if data['estimated_end_date'] else None
    if 'estimated_hours' in data:
        task.estimated_hours = float(data['estimated_hours'])
    if 'actual_hours' in data:
        task.actual_hours = float(data['actual_hours'])
    if 'assignee' in data:
        task.assignee = data.get('assignee') or None
    if 'priority' in data:
        task.priority = data['priority']
    if 'notes' in data:
        task.notes = data.get('notes')
    
    if 'status' in data and data['status'] != old_status:
        task.status = data['status']
        
        if task.project_id:
            project = Project.query.get(task.project_id)
            if project:
                all_tasks = project.tasks
                non_cancelled_tasks = [t for t in all_tasks if t.status != 'cancelled']
                if len(non_cancelled_tasks) > 0:
                    all_completed = all(t.status == 'completed' for t in non_cancelled_tasks)
                    any_in_progress = any(t.status in ['in_progress', 'delayed'] for t in non_cancelled_tasks)
                    
                    if all_completed:
                        project.status = 'completed'
                        if project.completed_quantity == 0:
                            project.completed_quantity = project.target_quantity
                    elif any_in_progress:
                        if project.status == 'pending' or project.status == 'paused':
                            project.status = 'in_progress'
        
        if task.order_id:
            order = Order.query.get(task.order_id)
            if order:
                all_tasks = order.tasks
                non_cancelled_tasks = [t for t in all_tasks if t.status != 'cancelled']
                if len(non_cancelled_tasks) > 0:
                    all_completed = all(t.status == 'completed' for t in non_cancelled_tasks)
                    any_delayed = any(t.status == 'delayed' for t in non_cancelled_tasks)
                    
                    if all_completed:
                        if order.status not in ['completed', 'cancelled']:
                            order.status = 'ready'
                    elif any_delayed and order.status not in ['completed', 'cancelled']:
                        if order.status == 'pending':
                            order.status = 'in_progress'
    
    if task.order_id and not task.project_id:
        order = Order.query.get(task.order_id)
        if order and order.project_id:
            task.project_id = order.project_id
    
    db.session.commit()
    return jsonify(task.to_dict())


@app.route('/api/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': '删除成功'})


@app.route('/api/tasks/schedule-conflicts', methods=['GET'])
def get_schedule_conflicts():
    conflicts = []
    tasks = Task.query.filter(
        Task.status.notin_(['completed', 'cancelled']),
        Task.estimated_start_date.isnot(None),
        Task.estimated_end_date.isnot(None)
    ).all()
    
    for i in range(len(tasks)):
        for j in range(i + 1, len(tasks)):
            t1, t2 = tasks[i], tasks[j]
            if t1.assignee and t1.assignee == t2.assignee:
                if t1.estimated_start_date <= t2.estimated_end_date and \
                   t2.estimated_start_date <= t1.estimated_end_date:
                    overlap_days = (min(t1.estimated_end_date, t2.estimated_end_date) - 
                                    max(t1.estimated_start_date, t2.estimated_start_date)).days + 1
                    conflicts.append({
                        'task1': t1.to_dict(),
                        'task2': t2.to_dict(),
                        'assignee': t1.assignee,
                        'overlap_days': overlap_days,
                        'message': f'负责人"{t1.assignee}"在同一时间段有重叠任务'
                    })
    
    return jsonify(conflicts)


@app.route('/api/statistics/task-overview', methods=['GET'])
def get_task_overview():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    total_tasks = Task.query.count()
    pending_tasks = Task.query.filter_by(status='pending').count()
    in_progress_tasks = Task.query.filter_by(status='in_progress').count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    delayed_tasks = Task.query.filter_by(status='delayed').count()
    
    this_week_tasks = Task.query.filter(
        Task.estimated_start_date >= week_start,
        Task.estimated_start_date <= week_end
    ).count()
    
    total_estimated_hours = db.session.query(func.sum(Task.estimated_hours)).scalar() or 0
    total_actual_hours = db.session.query(func.sum(Task.actual_hours)).scalar() or 0
    
    completed_projects = Project.query.filter_by(status='completed').all()
    total_completed_pieces = sum(p.completed_quantity for p in completed_projects)
    total_hours_for_completed = 0
    for p in completed_projects:
        total_hours_for_completed += sum(t.actual_hours or t.estimated_hours for t in p.tasks)
    
    avg_piece_hours = total_hours_for_completed / total_completed_pieces if total_completed_pieces > 0 else 0
    
    high_risk_count = 0
    high_risk_deliveries = []
    
    orders = Order.query.filter(
        Order.status.notin_(['completed', 'cancelled']),
        Order.delivery_date.isnot(None)
    ).all()
    
    for o in orders:
        risk = o.delay_risk
        if risk == 'high':
            high_risk_count += 1
            remaining_hours = sum(
                (t.estimated_hours or 0) - (t.actual_hours or 0)
                for t in o.tasks if t.status not in ['completed', 'cancelled']
            )
            high_risk_tasks = [t for t in o.tasks if t.status not in ['completed', 'cancelled']]
            task_name = high_risk_tasks[0].name if high_risk_tasks else '未分配'
            assignee = high_risk_tasks[0].assignee if high_risk_tasks and high_risk_tasks[0].assignee else '未分配'
            
            high_risk_deliveries.append({
                'type': 'order',
                'id': o.id,
                'name': o.customer_name,
                'task_name': task_name,
                'assignee': assignee,
                'due_date': o.delivery_date.isoformat() if o.delivery_date else None,
                'days_until_due': o.days_until_delivery,
                'task_progress': o.task_progress,
                'remaining_hours': round(max(0, remaining_hours), 1),
                'risk_level': risk
            })
    
    projects = Project.query.filter(
        Project.status.notin_(['completed', 'cancelled'])
    ).all()
    
    for p in projects:
        risk = p.delay_risk
        if risk == 'high':
            high_risk_count += 1
            remaining_hours = sum(
                (t.estimated_hours or 0) - (t.actual_hours or 0)
                for t in p.tasks if t.status not in ['completed', 'cancelled']
            )
            high_risk_tasks = [t for t in p.tasks if t.status not in ['completed', 'cancelled']]
            task_name = high_risk_tasks[0].name if high_risk_tasks else '未分配'
            assignee = high_risk_tasks[0].assignee if high_risk_tasks and high_risk_tasks[0].assignee else '未分配'
            due_date = None
            days_until_due = 0
            if high_risk_tasks and high_risk_tasks[0].estimated_end_date:
                due_date = high_risk_tasks[0].estimated_end_date.isoformat()
                days_until_due = (high_risk_tasks[0].estimated_end_date - today).days
            
            high_risk_deliveries.append({
                'type': 'project',
                'id': p.id,
                'name': p.name,
                'task_name': task_name,
                'assignee': assignee,
                'due_date': due_date,
                'days_until_due': days_until_due,
                'task_progress': p.task_progress,
                'remaining_hours': round(max(0, remaining_hours), 1),
                'risk_level': risk
            })
    
    high_risk_deliveries.sort(key=lambda x: x['days_until_due'])
    
    return jsonify({
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'delayed_tasks': delayed_tasks,
        'this_week_tasks': this_week_tasks,
        'total_estimated_hours': round(total_estimated_hours, 2),
        'total_actual_hours': round(total_actual_hours, 2),
        'avg_piece_hours': round(avg_piece_hours, 2),
        'high_risk_delivery_count': high_risk_count,
        'high_risk_deliveries': high_risk_deliveries,
        'week_todo_count': this_week_tasks,
        'avg_hours_per_item': round(avg_piece_hours, 2),
        'delayed_task_count': delayed_tasks
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9102, debug=True)
