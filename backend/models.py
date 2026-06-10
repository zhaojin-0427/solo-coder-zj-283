from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Material(db.Model):
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    material_type = db.Column(db.String(50), nullable=False)
    color_code = db.Column(db.String(50))
    width = db.Column(db.Float, nullable=False)
    total_length = db.Column(db.Float, nullable=False)
    remaining_length = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    supplier = db.Column(db.String(100))
    purchase_date = db.Column(db.Date, nullable=False)
    photo = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    usages = db.relationship('MaterialUsage', backref='material', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'material_type': self.material_type,
            'color_code': self.color_code,
            'width': self.width,
            'total_length': self.total_length,
            'remaining_length': self.remaining_length,
            'unit_price': self.unit_price,
            'supplier': self.supplier,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'photo': self.photo,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'usage_rate': 1 - (self.remaining_length / self.total_length) if self.total_length > 0 else 0,
            'days_since_purchase': (datetime.utcnow().date() - self.purchase_date).days if self.purchase_date else 0,
            'total_value': self.remaining_length * self.unit_price
        }


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='in_progress')
    target_quantity = db.Column(db.Integer, default=1)
    completed_quantity = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    material_usages = db.relationship('MaterialUsage', backref='project', cascade='all, delete-orphan')
    process_photos = db.relationship('ProcessPhoto', backref='project', cascade='all, delete-orphan')
    
    def to_dict(self):
        total_material_cost = sum(usage.total_cost for usage in self.material_usages)
        unit_cost = total_material_cost / self.completed_quantity if self.completed_quantity > 0 else total_material_cost
        
        return {
            'id': self.id,
            'name': self.name,
            'project_type': self.project_type,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'target_quantity': self.target_quantity,
            'completed_quantity': self.completed_quantity,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_material_cost': total_material_cost,
            'unit_material_cost': unit_cost,
            'material_count': len(self.material_usages),
            'photo_count': len(self.process_photos)
        }


class MaterialUsage(db.Model):
    __tablename__ = 'material_usages'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    used_length = db.Column(db.Float, nullable=False)
    cutting_loss = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def total_cost(self):
        if self.material:
            return (self.used_length + self.cutting_loss) * self.material.unit_price
        return 0
    
    @property
    def utilization_rate(self):
        total = self.used_length + self.cutting_loss
        if total > 0:
            return self.used_length / total
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'material_id': self.material_id,
            'material_name': self.material.name if self.material else None,
            'material_type': self.material.material_type if self.material else None,
            'color_code': self.material.color_code if self.material else None,
            'used_length': self.used_length,
            'cutting_loss': self.cutting_loss,
            'total_length': self.used_length + self.cutting_loss,
            'unit_price': self.material.unit_price if self.material else 0,
            'total_cost': self.total_cost,
            'utilization_rate': self.utilization_rate,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ProcessPhoto(db.Model):
    __tablename__ = 'process_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    stage = db.Column(db.String(50), nullable=False)
    stage_order = db.Column(db.Integer, default=0)
    photo = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    experience = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'stage': self.stage,
            'stage_order': self.stage_order,
            'photo': self.photo,
            'description': self.description,
            'experience': self.experience,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
