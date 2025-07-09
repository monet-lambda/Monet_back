from sqlalchemy       import Table, Column
from sqlalchemy       import Integer, Float, String
from sqlalchemy       import Sequence
from sqlalchemy       import ForeignKey
from sqlalchemy.orm   import relationship, backref

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

context_data_file = Table(
    'context_data_file', Base.metadata,
    Column('contextId',  Integer, ForeignKey('context.contextId'),        nullable = False),
    Column('dataFileId', Integer, ForeignKey('data_file.dataFileId'),     nullable = False)
)

run_data_file     = Table(
    'run_data_file',     Base.metadata,
    Column('runNumber',  Integer, ForeignKey('run.runNumber'),            nullable = False),
    Column('dataFileId', Integer, ForeignKey('data_file.dataFileId'),     nullable = False)
)
context_ref_file  = Table(
    'context_ref_file',  Base.metadata,
    Column('contextId',  Integer, ForeignKey('context.contextId'),        nullable = False),
    Column('refFileId',  Integer, ForeignKey('reference_file.refFileId'), nullable = False)
)

run_ref_file      = Table(
    'run_ref_file',      Base.metadata,
    Column('runNumber',  Integer, ForeignKey('run.runNumber'),            nullable = False),
    Column('refFileId',  Integer, ForeignKey('reference_file.refFileId'), nullable = False)
)
run_dq_flag       = Table(
    'run_dq_flag',       Base.metadata,
    Column('runNumber',  Integer, ForeignKey('run.runNumber'),            nullable = False, unique = True),
    Column('dqFlagId',   Integer, ForeignKey('dq_flags.dqFlagId'),        nullable = False, default = 15)
)

fill_data_property = Table(
    'fill_data_property', Base.metadata,
    Column('fillId',            Integer,  ForeignKey('fill.id'),                      nullable = False),
    Column('dataPropertyId',    Integer,  ForeignKey('data_property.dataPropertyId'), nullable = False),
    Column('dataPropertyValue', Float)
)
run_data_property  = Table(
    'run_data_property', Base.metadata,
    Column('runNumber',         Integer, ForeignKey('run.runNumber'),                nullable = False),
    Column('dataPropertyId',    Integer, ForeignKey('data_property.dataPropertyId'), nullable = False),
    Column('dataPropertyValue', Float)
)
procPass_data_file = Table(
    'processingPass_data_file', Base.metadata,
    Column('processingPassId',  Integer, ForeignKey('processing_pass.processingPassId'), nullable = False),
    Column('dataFileId',        Integer, ForeignKey('data_file.dataFileId'),            nullable = False)
)
procPass_ref_file  = Table(
    'processingPass_ref_file',  Base.metadata,
    Column('processingPassId',  Integer, ForeignKey('processing_pass.processingPassId'), nullable = False, unique=True),
    Column('refFileId',         Integer, ForeignKey('reference_file.refFileId'),        nullable = False)
)

class Context(Base):
    __tablename__ = 'context'

    contextId   = Column(Integer, Sequence('contextId_seq'), primary_key=True)
    contextName = Column(String(40), unique=True, nullable=False)

    dataFiles = relationship(
        'DataFile',
        secondary=context_data_file,
        backref=backref('contexts', uselist=True)
    )

    refFiles = relationship(
        'ReferenceFile',
        secondary=context_ref_file,
        backref=backref('contexts', uselist=True),
        uselist=True
    )

    def __repr__(self):
        return "<Context(contextName='%s)'>" %(self.contextName)


class Run(Base):
    __tablename__ = 'run'

    runNumber = Column(Integer, primary_key=True)
    fillId    = Column(Integer, ForeignKey('fill.id'), nullable=True)

    dataFile = relationship(
        'DataFile',
        secondary=run_data_file,
        backref=backref('run', uselist=False)
    )

    refFiles = relationship(
        'ReferenceFile',
        secondary=run_ref_file,
        backref=backref('runs', uselist=True),
        uselist=True
    )
    dqFlag = relationship(
        'DQFlags',
        secondary = run_dq_flag,
        uselist   = False
    )

    def __repr__(self):
        return "<Run(runNumber='%s')>" %(str(self.runNumber))


class Fill(Base):
    __tablename__ = 'fill'

    id   = Column(Integer, primary_key=True)
    runs = relationship(Run, backref=backref('fill'), uselist=True)

    def __repr__(self):
        return "<Fill(number='%s')>" %(str(self.id))


class DataFile(Base):
    __tablename__ = 'data_file'

    dataFileId   = Column(Integer, Sequence('datafile_id_seq'), primary_key=True)
    dataFilePath = Column(String(255), unique=True, nullable=False)

    def __repr__(self):
        return "<DataFile(dataFilePath='%s')>" %(self.dataFilePath)


class ReferenceFile(Base):
     __tablename__ = 'reference_file'

     refFileId   = Column(Integer, Sequence('refFile_id_seq'), primary_key=True)
     refFilePath = Column(String(255), unique=True, nullable=False)

     def __repr__(self):
         return "<ReferenceFile(refFilePath='%s')>" %(self.refFilePath)


class DQFlags(Base):
    __tablename__ = 'dq_flags'

    dqFlagId = Column(Integer, Sequence('dqFlag_id_seq'), primary_key=True)
    dqFlag   = Column(String(32), unique=True, nullable=False)

    def __repr__(self):
        return "<DQFlags(flag='%s')>" %(self.dqFlag)


class DataProperty(Base):
    __tablename__ = 'data_property'

    dataPropertyId = Column(Integer,     Sequence('dataProperty_id_seq'), primary_key=True)
    dataProperty   = Column(String(256), unique=True, nullable=False)

    def __repr__(self):
        return "<DataProperty(Property='%s')>" %(self.dataProperty)


class ProcessingPass(Base):
    __tablename__ = 'processing_pass'

    processingPassId = Column(Integer,   Sequence('processingPass_id_seq'), primary_key=True)
    processingPass   = Column(String(256), unique=True, nullable=False)

    dataFiles = relationship(
        DataFile,
         uselist=True,
         secondary=procPass_data_file,
         backref=backref('procPass')
    )

    refFiles = relationship(
        ReferenceFile,
        uselist=False,
        secondary=procPass_ref_file,
        backref=backref('procPass')
    )

    def __repr__(self):
        return "<ProcessingPass(Property='%s')>" %(self.processingPass)
#------------------------------------------------------------------------------------
"""
    Tables for simDQ
         
    \author  M. Adinolfi
    \version 1.0
"""

class SimCondition(Base):
    __tablename__ = 'sim_condition'

    simConditionId = Column(Integer,   Sequence('simCondition_id_seq'), primary_key=True)
    simCondition   = Column(String(256), unique=True, nullable=False)

    def __repr__(self):
        return "<SimCondition(simCondition='%s')>" %(self.simCondition)

class SimProcessingPass(Base):
    __tablename__ = 'sim_processing_pass'

    simProcessingPassId = Column(Integer,   Sequence('simProcessingPass_id_seq'), primary_key=True)
    simProcessingPass   = Column(String(256), unique=True, nullable=False)

    def __repr__(self):
        return "<SimProcessingPass(simProcessingPass='%s')>" %(self.simProcessingPass)

class EventType(Base):
    __tablename__ = 'event_type'

    eventType = Column(Integer, primary_key=True)

    def __repr__(self):
        return "<EventType(eventType='%d')>" %(self.eventType)
