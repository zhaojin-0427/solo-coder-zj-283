import os
from datetime import datetime, date
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from models import db, Material, Project, MaterialUsage, ProcessPhoto
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
        old_total = material.total_length
        diff = float(data['total_length']) - old_total
        material.total_length = float(data['total_length'])
        material.remaining_length += diff
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
    project = Project(
        name=data['name'],
        project_type=data['project_type'],
        description=data.get('description'),
        start_date=date.fromisoformat(data['start_date']),
        end_date=date.fromisoformat(data['end_date']) if data.get('end_date') else None,
        status=data.get('status', 'in_progress'),
        target_quantity=int(data.get('target_quantity', 1)),
        completed_quantity=int(data.get('completed_quantity', 0)),
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
    if 'target_quantity' in data:
        project.target_quantity = int(data['target_quantity'])
    if 'completed_quantity' in data:
        project.completed_quantity = int(data['completed_quantity'])
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9102, debug=True)
