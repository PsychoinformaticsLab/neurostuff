from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
import shortuuid

from ..database import db


def generate_id():
    return shortuuid.ShortUUID().random(length=12)


class BaseMixin(object):

    id = db.Column(db.Text, primary_key=True, default=generate_id)
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    @property
    def IRI(self):
        return f"http://neurostore.org/api/{self.__tablename__}/{self.id}"


class Dataset(BaseMixin, db.Model):
    __tablename__ = 'datasets'

    name = db.Column(db.String)
    description = db.Column(db.String)
    publication = db.Column(db.String)
    doi = db.Column(db.String)
    pmid = db.Column(db.String)
    public = db.Column(db.Boolean, default=True)
    nimads_data = db.Column(db.JSON)
    user_id = db.Column(db.Text, db.ForeignKey('users.id'))
    user = relationship('User', backref=backref('datasets'))


class Study(BaseMixin, db.Model):
    __tablename__ = 'studies'

    name = db.Column(db.String)
    description = db.Column(db.String)
    publication = db.Column(db.String)
    # source_url = db.Column(db.String)
    doi = db.Column(db.String)
    pmid = db.Column(db.String)
    public = db.Column(db.Boolean, default=True)
    metadata_ = db.Column(db.JSON)
    user_id = db.Column(db.Text, db.ForeignKey('users.id'))
    user = relationship('User', backref=backref('studies'))


class Analysis(BaseMixin, db.Model):
    __tablename__ = 'analyses'

    study_id = db.Column(db.Text, db.ForeignKey('studies.id'))
    name = db.Column(db.String)
    description = db.Column(db.String)
    # sample_size or meta-data (number of units unspecified, determine from entity table)
    # are people with groups
    study = relationship('Study', backref=backref('analyses'))
    conditions = association_proxy('analysis_conditions', 'condition')
    weights = association_proxy('analysis_conditions', 'weight')


class Condition(BaseMixin, db.Model):
    __tablename__ = 'conditions'

    name = db.Column(db.String)
    description = db.Column(db.String)


class AnalysisConditions(db.Model):
    __tablename__ = 'analysis_conditions'

    weight = db.Column(db.Float)
    analysis_id = db.Column(
        db.Text, db.ForeignKey('analyses.id'), primary_key=True)
    condition_id = db.Column(
        db.Text, db.ForeignKey('conditions.id'), primary_key=True)
    analysis = relationship('Analysis', backref=backref('analysis_conditions'))
    condition = relationship(
        'Condition', backref=backref('analysis_conditions'))


PointEntityMap = db.Table(
    'point_entities', db.Model.metadata,
    db.Column('point', db.Text, db.ForeignKey('points.id')),
    db.Column('entity', db.Text, db.ForeignKey('entities.id')))


ImageEntityMap = db.Table(
    'image_entities', db.Model.metadata,
    db.Column('image', db.Text, db.ForeignKey('images.id')),
    db.Column('entity', db.Text, db.ForeignKey('entities.id')))


# purpose of Entity: you have an image/coordinate, but you do not
# know where it was from
class Entity(BaseMixin, db.Model):
    __tablename__ = 'entities'

    study_id = db.Column(db.Text, db.ForeignKey("studies.id")) # link to analysis
    analysis_id = db.Column(db.Text, db.ForeignKey("analyses.id"))
    label = db.Column(db.String)
    level = db.Column(db.String)
    data = db.Column(db.JSON) # metadata
    study = relationship('Study', backref=backref('entities'))
    analysis = relationship('Analysis', backref=backref('entities'))


class Point(BaseMixin, db.Model):
    __tablename__ = 'points'

    @property
    def coordinates(self):
        return [self.x, self.y, self.z]

    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)
    space = db.Column(db.String)
    kind = db.Column(db.String)
    image = db.Column(db.String)
    label_id = db.Column(db.Float, default=None)
    analysis_id = db.Column(db.Text, db.ForeignKey('analyses.id'))

    entities = relationship("Entity", secondary=PointEntityMap,
                            backref=backref("points"))
    analysis = relationship("Analysis", backref=backref("points"))


class Image(BaseMixin, db.Model):
    __tablename__ = 'images'

    url = db.Column(db.String)
    filename = db.Column(db.String)
    space = db.Column(db.String)
    value_type = db.Column(db.String)
    analysis_id = db.Column(db.Text, db.ForeignKey('analyses.id'))
    data = db.Column(db.JSON)
    add_date = db.Column(db.DateTime(timezone=True))

    analysis_name = association_proxy('analysis', 'name')
    entities = relationship("Entity", secondary=ImageEntityMap,
                            backref=backref("images"))
    analysis = relationship("Analysis", backref=backref("images"))


class PointValue(BaseMixin, db.Model):
    __tablename__ = 'point_values'

    point_id = db.Column(db.Text, db.ForeignKey('points.id'))
    kind = db.Column(db.String)
    value = db.Column(db.String)
    dtype = db.Column(db.String, default='str')
    point = relationship('Point', backref=backref('values'))


# Annotation Database
class Annotation(BaseMixin, db.Model):
    __tablename__ = "annotations"

    annotations = db.Column(db.Text)
    user_id = db.Column(db.Text, db.ForeignKey('users.id'))
    user = relationship('User', backref=backref('annotations'))
    dataset_id = db.Column(db.Text, db.ForeignKey('datasets.id'))
    dataset = relationship('Dataset', backref=backref('annotations'))
