from datetime import datetime, date, timedelta
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
    
    @property
    def is_used(self):
        return len(self.usages) > 0
    
    @property
    def used_length_total(self):
        return sum(usage.used_length + usage.cutting_loss for usage in self.usages)
    
    @property
    def used_by_projects(self):
        seen = set()
        result = []
        for usage in self.usages:
            if usage.project_id not in seen:
                seen.add(usage.project_id)
                result.append({'project_id': usage.project_id, 'project_name': usage.project.name})
        return result
    
    @property
    def used_project_count(self):
        return len(self.used_by_projects)
    
    def to_dict(self):
        usage_rate = 1 - (self.remaining_length / self.total_length) if self.total_length > 0 else 0
        usage_rate = min(usage_rate, 1.0)
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
            'usage_rate': usage_rate,
            'days_since_purchase': (datetime.utcnow().date() - self.purchase_date).days if self.purchase_date else 0,
            'total_value': max(0, self.remaining_length * self.unit_price),
            'is_used': self.is_used,
            'used_length_total': self.used_length_total,
            'used_by_projects': self.used_by_projects
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
    tasks = db.relationship('Task', backref='project', cascade='all, delete-orphan')
    
    @property
    def progress_percentage(self):
        if self.target_quantity <= 0:
            return 0
        quantity_progress = self.completed_quantity / self.target_quantity * 100
        
        if len(self.tasks) > 0:
            total_hours = sum(t.estimated_hours for t in self.tasks)
            if total_hours > 0:
                completed_hours = sum(t.estimated_hours for t in self.tasks if t.status == 'completed')
                in_progress_hours = sum(t.estimated_hours * 0.5 for t in self.tasks if t.status == 'in_progress')
                task_progress = (completed_hours + in_progress_hours) / total_hours * 100
            else:
                completed = sum(1 for t in self.tasks if t.status == 'completed')
                task_progress = completed / len(self.tasks) * 100
            return min(100, round(quantity_progress * 0.3 + task_progress * 0.7))
        
        return min(100, round(quantity_progress))
    
    @property
    def task_progress(self):
        if len(self.tasks) == 0:
            return None
        total_hours = sum(t.estimated_hours for t in self.tasks)
        if total_hours == 0:
            completed = sum(1 for t in self.tasks if t.status == 'completed')
            return round(completed / len(self.tasks) * 100, 1)
        completed_hours = sum(t.estimated_hours for t in self.tasks if t.status == 'completed')
        in_progress_hours = sum(t.estimated_hours * 0.5 for t in self.tasks if t.status == 'in_progress')
        return round((completed_hours + in_progress_hours) / total_hours * 100, 1)
    
    @property
    def is_over_target(self):
        return self.completed_quantity > self.target_quantity
    
    @property
    def task_count(self):
        return len(self.tasks)
    
    @property
    def completed_task_count(self):
        return sum(1 for t in self.tasks if t.status == 'completed')
    
    @property
    def in_progress_task_count(self):
        return sum(1 for t in self.tasks if t.status == 'in_progress')
    
    @property
    def delayed_task_count(self):
        return sum(1 for t in self.tasks if t.status == 'delayed')
    
    @property
    def total_estimated_hours(self):
        return sum(t.estimated_hours for t in self.tasks)
    
    @property
    def total_actual_hours(self):
        return sum(t.actual_hours or 0 for t in self.tasks)
    
    @property
    def schedule_conflicts(self):
        conflicts = []
        tasks = self.tasks
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                t1, t2 = tasks[i], tasks[j]
                if t1.estimated_start_date and t1.estimated_end_date and \
                   t2.estimated_start_date and t2.estimated_end_date and \
                   t1.assignee == t2.assignee and \
                   t1.status not in ['completed', 'cancelled'] and \
                   t2.status not in ['completed', 'cancelled']:
                    if t1.estimated_start_date <= t2.estimated_end_date and \
                       t2.estimated_start_date <= t1.estimated_end_date:
                        conflicts.append({
                            'task1_id': t1.id,
                            'task1_name': t1.name,
                            'task2_id': t2.id,
                            'task2_name': t2.name,
                            'assignee': t1.assignee,
                            'overlap_days': (min(t1.estimated_end_date, t2.estimated_end_date) - max(t1.estimated_start_date, t2.estimated_start_date)).days + 1,
                            'message': f'负责人"{t1.assignee}"在同一时间段有重叠任务'
                        })
        return conflicts
    
    @property
    def delay_risk(self):
        if self.status == 'completed':
            return 'none'
        if len(self.tasks) == 0:
            return 'none'
        
        today = date.today()
        delayed_tasks = self.delayed_task_count
        
        if delayed_tasks > 0:
            return 'high'
        
        if self.end_date:
            days_left = (self.end_date - today).days
            remaining_hours = sum(t.estimated_hours for t in self.tasks if t.status not in ['completed', 'cancelled'])
            estimated_days_needed = remaining_hours / 8
            
            if days_left < 0:
                return 'high'
            elif estimated_days_needed > days_left * 1.5:
                return 'high'
            elif estimated_days_needed > days_left:
                return 'medium'
        
        return 'low'
    
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
            'photo_count': len(self.process_photos),
            'progress_percentage': self.progress_percentage,
            'is_over_target': self.is_over_target,
            'task_progress': self.task_progress,
            'task_count': self.task_count,
            'completed_task_count': self.completed_task_count,
            'in_progress_task_count': self.in_progress_task_count,
            'delayed_task_count': self.delayed_task_count,
            'total_estimated_hours': self.total_estimated_hours,
            'total_actual_hours': self.total_actual_hours,
            'schedule_conflicts': self.schedule_conflicts,
            'delay_risk': self.delay_risk
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


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(200), nullable=False)
    order_source = db.Column(db.String(50))
    requirement = db.Column(db.Text)
    delivery_date = db.Column(db.Date)
    quoted_price = db.Column(db.Float, default=0)
    deposit = db.Column(db.Float, default=0)
    balance = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = db.relationship('Project', backref='orders')
    
    @property
    def is_overdue(self):
        if not self.delivery_date:
            return False
        if self.status in ['completed', 'cancelled']:
            return False
        return date.today() > self.delivery_date
    
    @property
    def days_until_delivery(self):
        if not self.delivery_date:
            return None
        return (self.delivery_date - date.today()).days
    
    @property
    def material_cost(self):
        if not self.project:
            return 0
        return sum(usage.total_cost for usage in self.project.material_usages)
    
    @property
    def suggested_price(self):
        cost = self.material_cost
        if cost <= 0:
            return 0
        if cost < 100:
            return cost * 2.5
        elif cost < 500:
            return cost * 2.0
        else:
            return cost * 1.8
    
    @property
    def profit_estimate(self):
        return self.quoted_price - self.material_cost
    
    @property
    def profit_margin(self):
        if self.quoted_price <= 0:
            return 0
        return (self.profit_estimate / self.quoted_price) * 100
    
    @property
    def delivery_risk(self):
        if self.status in ['completed', 'cancelled']:
            return 'none'
        if not self.delivery_date:
            return 'medium'
        days_left = self.days_until_delivery
        if days_left is None:
            return 'medium'
        if days_left < 0:
            return 'high'
        if self.project and self.project.status != 'completed':
            progress = self.project.progress_percentage
            if days_left <= 3 and progress < 80:
                return 'high'
            elif days_left <= 7 and progress < 50:
                return 'high'
            elif days_left <= 14 and progress < 30:
                return 'medium'
        return 'low'
    
    @property
    def task_progress(self):
        if not self.project or len(self.project.tasks) == 0:
            return None
        tasks = self.project.tasks
        total_hours = sum(t.estimated_hours for t in tasks)
        if total_hours == 0:
            completed = sum(1 for t in tasks if t.status == 'completed')
            return completed / len(tasks) * 100
        completed_hours = sum(t.estimated_hours for t in tasks if t.status == 'completed')
        in_progress_hours = sum(t.estimated_hours * 0.5 for t in tasks if t.status == 'in_progress')
        return (completed_hours + in_progress_hours) / total_hours * 100

    @property
    def task_count(self):
        if not self.project:
            return 0
        return len(self.project.tasks)

    @property
    def completed_task_count(self):
        if not self.project:
            return 0
        return sum(1 for t in self.project.tasks if t.status == 'completed')

    @property
    def delayed_task_count(self):
        if not self.project:
            return 0
        return sum(1 for t in self.project.tasks if t.status == 'delayed')

    @property
    def schedule_conflicts(self):
        conflicts = []
        if not self.project:
            return conflicts
        tasks = self.project.tasks
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                t1, t2 = tasks[i], tasks[j]
                if t1.estimated_start_date and t1.estimated_end_date and \
                   t2.estimated_start_date and t2.estimated_end_date and \
                   t1.assignee == t2.assignee and \
                   t1.status not in ['completed', 'cancelled'] and \
                   t2.status not in ['completed', 'cancelled']:
                    if t1.estimated_start_date <= t2.estimated_end_date and \
                       t2.estimated_start_date <= t1.estimated_end_date:
                        conflicts.append({
                            'task1_id': t1.id,
                            'task1_name': t1.name,
                            'task2_id': t2.id,
                            'task2_name': t2.name,
                            'assignee': t1.assignee,
                            'message': f'负责人"{t1.assignee}"在同一时间段有重叠任务'
                        })
        return conflicts

    @property
    def delay_risk(self):
        if self.status in ['completed', 'cancelled']:
            return 'none'
        if not self.project or len(self.project.tasks) == 0:
            return 'none'
        
        today = date.today()
        total_tasks = len(self.project.tasks)
        delayed_tasks = self.delayed_task_count
        remaining_tasks = sum(1 for t in self.project.tasks if t.status not in ['completed', 'cancelled'])
        
        if delayed_tasks > 0:
            return 'high'
        
        if self.delivery_date:
            days_left = (self.delivery_date - today).days
            remaining_hours = sum(t.estimated_hours for t in self.project.tasks if t.status not in ['completed', 'cancelled'])
            estimated_days_needed = remaining_hours / 8
            
            if days_left < 0:
                return 'high'
            elif estimated_days_needed > days_left * 1.5:
                return 'high'
            elif estimated_days_needed > days_left:
                return 'medium'
        
        return 'low'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'contact_info': self.contact_info,
            'order_source': self.order_source,
            'requirement': self.requirement,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'quoted_price': self.quoted_price,
            'deposit': self.deposit,
            'balance': self.balance,
            'status': self.status,
            'notes': self.notes,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'project_status': self.project.status if self.project else None,
            'project_progress': self.project.progress_percentage if self.project else 0,
            'material_cost': self.material_cost,
            'suggested_price': self.suggested_price,
            'profit_estimate': self.profit_estimate,
            'profit_margin': round(self.profit_margin, 2),
            'is_overdue': self.is_overdue,
            'days_until_delivery': self.days_until_delivery,
            'delivery_risk': self.delivery_risk,
            'photo_count': len(self.project.process_photos) if self.project else 0,
            'task_progress': self.task_progress,
            'task_count': self.task_count,
            'completed_task_count': self.completed_task_count,
            'delayed_task_count': self.delayed_task_count,
            'schedule_conflicts': self.schedule_conflicts,
            'delay_risk': self.delay_risk,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    stage = db.Column(db.String(50), nullable=False)
    estimated_start_date = db.Column(db.Date)
    estimated_end_date = db.Column(db.Date)
    estimated_hours = db.Column(db.Float, default=0)
    actual_hours = db.Column(db.Float, default=0)
    assignee = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order = db.relationship('Order', backref='tasks')
    
    @property
    def is_overdue(self):
        if self.status in ['completed', 'cancelled']:
            return False
        if not self.estimated_end_date:
            return False
        return date.today() > self.estimated_end_date
    
    @property
    def days_until_deadline(self):
        if not self.estimated_end_date:
            return None
        return (self.estimated_end_date - date.today()).days
    
    @property
    def progress(self):
        if self.status == 'completed':
            return 100
        elif self.status == 'in_progress':
            if self.estimated_hours > 0 and self.actual_hours > 0:
                return min(95, round(self.actual_hours / self.estimated_hours * 100))
            return 50
        elif self.status == 'delayed':
            return 30
        return 0
    
    @property
    def schedule_conflicts(self):
        conflicts = []
        if self.status in ['completed', 'cancelled'] or not self.assignee:
            return conflicts
        if not self.estimated_start_date or not self.estimated_end_date:
            return conflicts
        
        query = Task.query.filter(
            Task.id != self.id,
            Task.assignee == self.assignee,
            Task.status.notin_(['completed', 'cancelled']),
            Task.estimated_start_date.isnot(None),
            Task.estimated_end_date.isnot(None)
        )
        
        for other in query.all():
            if self.estimated_start_date <= other.estimated_end_date and \
               other.estimated_start_date <= self.estimated_end_date:
                conflicts.append({
                    'task_id': other.id,
                    'task_name': other.name,
                    'assignee': other.assignee,
                    'overlap_days': (min(self.estimated_end_date, other.estimated_end_date) - 
                                     max(self.estimated_start_date, other.estimated_start_date)).days + 1,
                    'message': f'与任务"{other.name}"时间重叠'
                })
        
        return conflicts
    
    @property
    def delay_risk(self):
        if self.status in ['completed', 'cancelled']:
            return 'none'
        if self.status == 'delayed':
            return 'high'
        
        if self.estimated_end_date:
            days_left = (self.estimated_end_date - date.today()).days
            remaining_hours = self.estimated_hours - (self.actual_hours or 0)
            estimated_days_needed = remaining_hours / 8
            
            if days_left < 0:
                return 'high'
            elif estimated_days_needed > days_left * 1.5:
                return 'high'
            elif estimated_days_needed > days_left:
                return 'medium'
        
        if self.priority == 'high' and self.status == 'pending':
            return 'medium'
        
        return 'low'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'order_id': self.order_id,
            'order_customer': self.order.customer_name if self.order else None,
            'stage': self.stage,
            'estimated_start_date': self.estimated_start_date.isoformat() if self.estimated_start_date else None,
            'estimated_end_date': self.estimated_end_date.isoformat() if self.estimated_end_date else None,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'assignee': self.assignee,
            'priority': self.priority,
            'status': self.status,
            'notes': self.notes,
            'is_overdue': self.is_overdue,
            'days_until_deadline': self.days_until_deadline,
            'progress': self.progress,
            'schedule_conflicts': self.schedule_conflicts,
            'delay_risk': self.delay_risk,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
