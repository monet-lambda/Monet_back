from .models import *
import sqlalchemy
from sqlalchemy.orm   import sessionmaker, scoped_session
from sqlalchemy       import desc, or_


class DQ_DB(object):
    def __init__(self, address):
        self.address      = address
        self.engine = sqlalchemy.create_engine(self.address, echo=False)


        self.session = scoped_session(sessionmaker(autocommit=False, bind=self.engine))
        Base.query = self.session.query_property()
        self.base  = Base()

        self.offlineDQContextName = 'OfflineDQ'
        self.onlineDQContextName  = 'OnlineDQ'

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'engine'):
            self.engine.dispose()

        try:
            super(DQ_DB, self).__del__()
        except AttributeError:
            pass

    def addOfflineDQFileWithProcPass(self, processingPass, path, commit=False):
        insFile  = self.insertDataFile(path)
        dataFile = insFile['datafile']

        insProcPass = self.insertProcessingPass(processingPass)
        procPass    = insProcPass['processingPass']

        if insFile['Added'] or insProcPass['Added']:
            self.commit()

        #
        # Check the OfflineDQ context and the processing pass are
        # set for this file.
        #

        hasOfflineDQ = False
        for c in dataFile.contexts:
            if c.contextName == self.offlineDQContextName:
                hasOfflineDQ = True

        if not hasOfflineDQ:
            context = self.getContext(self.offlineDQContextName)
            dataFile.contexts.append(context)

        hasProcPass = False
        for p in dataFile.procPass:
            if p.processingPass == procPass:
                hasProcPass = True

        if not hasProcPass:
            dataFile.procPass.append(procPass)

        if not hasOfflineDQ or not hasProcPass:
            try:
                self.session.add(dataFile)
                if commit:
                    self.commit()
            except:
                self.rollback()
                raise

        return dataFile

    def addOfflineDQFileForRunWithProcPass(self, run, processingPass, path, commit=False):
        dataFile = self.addOfflineDQFileWithProcPass(processingPass, path, commit)

        if dataFile.run is None:
            if type(run) is int:
                run = self.getRun(run)
            elif type(run) is str:
                run = self.getRun(int(run))

            if run is None:
                return None

            dataFile.run = run
            try:
                self.session.add(dataFile)
                if commit:
                    self.commit()
            except:
                self.rollback()
                raise

        return dataFile

    def addOfflineDQRefFile(self, run, processingPass, path, commit=False):
        refFile = self.addOfflineDQRefFileWithProcPass(processingPass, path)

        if refFile is None:
            return None
        
        if type(run) is int:
            run = self.getRun(run)
        elif type(run) is str:
            run = self.getRun(int(run))

        if run is None:
            return None
        
        hasRun = False
        for r in refFile.runs:
            if r.runNumber == run.runNumber:
                hasRun = True
                break
        
        if not hasRun:
            try:
                refFile.runs.append(run)
                self.session.add(refFile)
                if commit:
                    self.commit()
            except:
                self.rollback()
                raise
        return refFile

    def addOfflineDQRefFileWithProcPass(self, processingPass, path):
        insFile = self.insertRefFile(path)
        refFile = insFile['refFile']
            
        insProcPass = self.insertProcessingPass(processingPass)
        procPass    = insProcPass['processingPass']

        if insFile['Added'] or insProcPass['Added']:
            try:
                self.commit()
            except:
                self.rollback()
                raise

        #
        # Check the run, the context and the processing pass are known
        #

        hasOfflineDQ = False
        for c in refFile.contexts:
            if c.contextName == self.offlineDQContextName:
                hasOfflineDQ = True
                break

        hasProcPass = False
        for p in refFile.procPass:
            if p.processingPass == procPass:
                hasProcPass = True

        #
        # If the run, the context or the processing pass
        # were not known add them.
        #

        needToAdd = False

        if not hasOfflineDQ:
            needToAdd = True
            context   = self.getContext(self.offlineDQContextName)
            refFile.contexts.append(context)

        if not hasProcPass:
            needToAdd = True
            refFile.procPass.append(procPass)

        if needToAdd:
            try:
                self.session.add(refFile)
                self.commit()
            except:
                self.rollback()
                raise
        
        return refFile

    def addOnlineDQFile(self, path):
        ins      = self.insertDataFile(path)
        dataFile = ins['datafile']

        if ins['Added']:
            self.commit()

        hasOnlineDQ = False
        for c in dataFile.contexts:
            if c.contextName == self.onlineDQContextName:
                hasOnlineDQ = True
                break

        if not hasOnlineDQ:
            context = self.getContext(self.onlineDQContextName)
            dataFile.contexts.append(context)
            self.session.add(dataFile)
            self.commit()

        return dataFile

    def addOnlineDQFileForRun(self, run, path, commit=False):
        dataFile = self.addOnlineDQFile(path)
        if dataFile.run is None:
            dataFile.run = run
            self.session.add(dataFile)
            if commit:
                self.commit()

        return dataFile

    def addOnlineDQRefFile(self, run, path, commit=False):
        ins     = self.insertRefFile(path)
        refFile = ins['refFile']

        if ins['Added']:
            self.commit()
        #
        # Check the run and context are known
        #

        hasRun = False
        for r in refFile.runs:
            if r.runNumber == run.runNumber:
                hasRun = True
                break


        hasOnlineDQ = False
        for c in refFile.contexts:
            if c.contextName == self.onlineDQContextName:
                hasOnlineDQ = True
                break
        #
        # If either the run or the context were not known add them
        #

        needToAdd = False

        if not hasRun:
            needToAdd = True
            refFile.runs.append(run)

        if not hasOnlineDQ:
            needToAdd = True
            context   = self.getContext(self.onlineDQContextName)
            refFile.contexts.append(context)

        if needToAdd:
            self.session.add(refFile)
            if commit:
                self.commit()

        return refFile

    def commit(self):
        self.session.commit()
        return


    def create_all(self):
        self.base.metadata.create_all(bind=self.engine)
        print((list(self.base.metadata.tables.keys())))
        return
#------------------------------------------------------------------------------------
    def deleteDataProcessingPass(self, processingPass, commit=False):
        """
         \author  M. Adinolfi
         \version 1.0
        """

        try:
            p = self.session.query(ProcessingPass).filter_by(processingPass=processingPass).first()
            if p:
                self.session.delete(p)
                if commit:
                    self.commit()
        except:
            self.rollback()
            raise            
#------------------------------------------------------------------------------------
    def deleteDataProperty(self, propertyName):
        """
         \author  M. Adinolfi
         \version 1.0
        """

        p = self.session.query(DataProperty).filter_by(dataProperty=propertyName).first()
        if p:
            self.session.delete(p)

        return
#------------------------------------------------------------------------------------
    def deleteEventType(self, eventType, commit=False):
        """
         \author  M. Adinolfi
         \version 1.0
        """

        try:
            if type(eventType) is str:
                eventType = int(eventType)
                
            p = self.session.query(EventType).filter_by(eventType=eventType).first()
            if p:
                self.session.delete(p)
                if commit:
                    self.commit()
        except:
            self.rollback()
            raise            
#------------------------------------------------------------------------------------
    def deleteFillPropertyErrValue(self, fill, propertyName):
        try:
            errName = propertyName + '_err'
            res = self.deleteFillPropertyValue(fill, errName)
            if not res:
                return False

            res = self.deleteFillPropertyValue(fill, propertyName)
            if not res:
                return False

            return True
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def deleteFillPropertyValue(self, fill, propertyName, commit=False):
        try:
            if type(fill)   is int:
                fill = self.getFill(fill)
            elif type(fill) is str:
                fill = self.getFill(int(fill))

            if fill is None:
                return False

            propertyId = self.getDataPropertyId(propertyName)
            if propertyId is None:
                return False

            d = fill_data_property.delete()
            d = d.where(fill_data_property.c.fillId==fill.id)
            d = d.where(fill_data_property.c.dataPropertyId==propertyId)

            res = self.session.execute(d)
            if commit:
                self.commit()
            return True
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def deleteRunDataFile(self, runNumber, path, commit=False):
        run = self.getRun(runNumber)
        if run is None:
            return False

        dataFile = self.getDataFile(path)
        if dataFile is None:
            return False

        d = run_data_file.delete()
        d = d.where(run_data_file.c.runNumber==run.runNumber)
        d = d.where(run_data_file.c.dataFileId==dataFile.dataFileId)

        res = self.session.execute(d)
        if commit:
            self.commit()

        return True
#------------------------------------------------------------------------------------
    def deleteRunPropertyErrValue(self, runNumber, propertyName, commit=False):
        try:
            errName = propertyName + '_err'

            res = self.deleteRunPropertyValue(runNumber, errName, commit)
            if not res:
                return False

            res = self.deleteRunPropertyValue(runNumber, propertyName, commit)
            if not res:
                return False

            return True
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def deleteRunPropertyValue(self, runNumber, propertyName, commit=False):
        try:
            propertyId = self.getDataPropertyId(propertyName)
            if propertyId is None:
                return False

            d = run_data_property.delete()
            d = d.where(run_data_property.c.runNumber==runNumber)
            d = d.where(run_data_property.c.dataPropertyId==propertyId)

            res = self.session.execute(d)
            if commit:
                self.commit()


            return True
        except:
            self.rollback()
            raise

#------------------------------------------------------------------------------------
    def deleteSimCondition(self, simCondition, commit=False):
        """
         \author  M. Adinolfi
         \version 1.0
        """

        try:
            p = self.session.query(SimCondition).filter_by(simCondition=simCondition).first()
            if p:
                self.session.delete(p)
                if commit:
                    self.commit()
        except:
            self.rollback()
            raise            
#------------------------------------------------------------------------------------
    def deleteSimProcessingPass(self, processingPass, commit=False):
        """
         \author  M. Adinolfi
         \version 1.0
        """

        try:
            p = self.session.query(SimProcessingPass).filter_by(simProcessingPass=processingPass).first()
            if p:
                self.session.delete(p)
                if commit:
                    self.commit()
        except:
            self.rollback()
            raise            

    def drop_all(self):
        self.commit()
        self.base.metadata.drop_all(bind=self.engine)
        return

    def drop_table(self, table, commit=False):
        smt = "DROP TABLE \"%s\"" %(table)
        s = self.session.execute(smt)
        if commit:
            self.commit()
        return

    def getContext(self, name):
        try:
            return self.session.query(Context).filter_by(contextName=name).first()
        except:
            self.rollback()
            raise

    def getContextId(self, name):
        try:
            contextId = None

            s = self.session.query(Context).filter_by(contextName=name)
            for r in s:
                contextId = r.contextId
            return contextId
        except:
            self.rollback()
            raise

    def getDataFile(self, path):
        try:
            dataFile = self.session.query(DataFile).filter_by(dataFilePath=path).first()

            if dataFile:
                return dataFile
            else:
                return None
        except:
            self.rollback()
            raise

    def getRefFile(self, path):
        try:
            refFile = self.session.query(ReferenceFile).filter_by(refFilePath=path).first()

            if refFile:
                return refFile
            else:
                return None
        except:
            self.rollback()
            raise

    def getDataFileId(self, path):
        try:
            dataFileId = None

            dataFile = self.session.query(DataFile).filter_by(dataFilePath=path).first()
            if dataFile:
                dataFileId =  dataFile.dataFileId

            return dataFileId
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def getDataProperties(self):
        try:
            dp = []
            q = self.session.query(DataProperty)
            for r in q:
                dp.append(r.dataProperty)
            return dp
        except:
            self.rollback()
            raise
    def getDataProperty(self, name):
        try:
            dp = self.session.query(DataProperty).filter_by(dataProperty=name).first()
            return dp
        except:
            self.rollback()
            raise
    def getDataPropertyId(self, name):
        try:
            propertyId = None

            s = self.session.query(DataProperty).filter_by(dataProperty=name)
            for r in s:
                propertyId = r.dataPropertyId
            return propertyId
        except:
            self.rollback()
            raise
    def getDQFlagId(self, flag):
        try:
            dqFlagId = None

            dqFlag = self.session.query(DQFlags).filter_by(dqFlag=flag).first()
            if dqFlag:
                dqFlagId =  dqFlag.dqFlagId

            return dqFlagId
        except:
            self.rollback()
            raise

#------------------------------------------------------------------------------------
    def getEventType(self, eventType):
        try:
            eType = self.session.query(EventType).filter_by(eventType=eventType).first()
            return eType
        except:
            self.rollback()
            raise
    def getEventTypes(self, eLow=0, eHigh=99999999):
        try:
            eTypes = []
            for row in self.session.query(EventType).   \
                    filter(EventType.eventType>=eLow).  \
                    filter(EventType.eventType<=eHigh). \
                    order_by(EventType.eventType):
                eTypes.append(row.eventType)
            return eTypes
        except:
            self.rollback()
            raise
    def getFill(self, fillId):
        try:
            fill = self.session.query(Fill).filter_by(id=fillId).first()
            return fill
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def getFillPropertyValue(self, propertyName, fillId):
        try:
            value = None

            propertyId = self.getDataPropertyId(propertyName)
            if propertyId is None:
                return value

            s = fill_data_property.select()
            s = s.where(fill_data_property.c.fillId==fillId)
            s = s.where(fill_data_property.c.dataPropertyId==propertyId)

            res = self.session.execute(s)
            for row in res:
                value = row[2]

            return value
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def getFills(self, fillLow=0, fillHigh=99999999):
        try:
            fills = []
            for row in self.session.query(Fill).   \
                        filter(Fill.id>=fillLow).  \
                        filter(Fill.id<=fillHigh). \
                        order_by(Fill.id):
                fills.append(row.id)
            return fills
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def getFillsPropertyValue(self, propertyName, fillLow=0, fillHigh=99999999):
        try:
            values = []

            propertyId = self.getDataPropertyId(propertyName)
            if propertyId is None:
                return values

            s = fill_data_property.select()
            s = s.where(fill_data_property.c.fillId>=fillLow)
            s = s.where(fill_data_property.c.fillId<=fillHigh)
            s = s.where(fill_data_property.c.dataPropertyId==propertyId)
            s = s.order_by(fill_data_property.c.fillId)

            res = self.session.execute(s)
            for row in res:
                value = [row[0],row[2]]
                values.append(value)

            res.close()
            return values
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def getFillsPropertyValueWithErr(self, propertyName, fillLow=0, fillHigh=99999999):
        retval = {'OK'     : 0,
                  'values' : {}}

        propertyId = self.getDataPropertyId(propertyName)
        if propertyId is None:
            retval['OK'] = 1
            return retval

        propertyErr   = propertyName + '_err'
        propertyErrId = self.getDataPropertyId(propertyErr)
        if propertyErr is None:
            retval['OK'] = 2
            return retval

        s = fill_data_property.select()
        s = s.where(fill_data_property.c.fillId>=fillLow)
        s = s.where(fill_data_property.c.fillId<=fillHigh)
        s = s.where(or_(fill_data_property.c.dataPropertyId==propertyId,fill_data_property.c.dataPropertyId==propertyErrId))
        s = s.order_by(fill_data_property.c.fillId)
        res = self.session.execute(s)

        for row in res:
            fillId = str(row[0])
            if fillId not in retval['values']:
                retval['values'][fillId] = [0,0]

            if row[1] == propertyId:
                retval['values'][fillId][0] = row[2]
            elif row[1] == propertyErrId:
                retval['values'][fillId][1] = row[2]

        res.close()

        return retval
#------------------------------------------------------------------------------------
    def getOfflineDQFile(self, runNumber):
        ref = self.getRunFileData(runNumber, self.offlineDQContextName)
        return ref

    def getOfflineDQFileWithProcPass(self, runNumber, processingPass):
        ref = self.getRunFileDataWithProcPass(runNumber, self.offlineDQContextName, processingPass)
        return ref

    def getOfflineDQFiles(self, runNumber):
        ref = self.getRunFilesData(runNumber, self.offlineDQContextName)
        return ref

    def getOfflineDQFilesWithProcPass(self, runNumber, processingPass):
        ref = self.getRunFilesDataWithProcPass(runNumber, self.offlineDQContextName, processingPass)
        return ref

    def getOfflineDQRef(self, runNumber):
        ref = self.getRunFileRef(runNumber, self.offlineDQContextName)
        return ref
    def getOfflineDQRefForProcPass(self, processingPass):
        ref = None
        try:
            ref = self.session.query(ReferenceFile).\
                  filter(ReferenceFile.procPass.any(processingPass=processingPass)).all()
        except:
            self.rollback()
            raise
        return ref
    def getOfflineDQRefWithProcPass(self, runNumber, processingPass):
        ref = self.getRunFileRefWithProcPass(runNumber, self.offlineDQContextName, processingPass)
        return ref
    def getOfflineDQRefs(self, runNumber):
        ref = self.getRunFilesRef(runNumber, self.offlineDQContextName)
        return ref

    def getOnlineDQFile(self, runNumber):
        ref = self.getRunFileData(runNumber, self.onlineDQContextName)
        return ref

    def getOnlineDQFiles(self, runNumber):
        ref = self.getRunFilesData(runNumber, self.onlineDQContextName)
        return ref

    def getOnlineDQRef(self, runNumber):
        ref = self.getRunFileRef(runNumber, self.onlineDQContextName)
        return ref

    def getOnlineDQRefs(self, runNumber):
        ref = self.getRunFilesRef(runNumber, self.onlineDQContextName)
        return ref

    def getProcessingPasses(self):
        try:
            procPass = []
            q = self.session.query(ProcessingPass)
            for r in q:
                procPass.append(r.processingPass)
            return procPass
        except:
            self.rollback()
            raise

    def getRun(self, runNumber):
        try:
            run = self.session.query(Run).filter_by(runNumber=runNumber).first()
            return run
        except:
            self.rollback()
            raise

    def getRunFileData(self, runNumber, contextName):
        dataFile = self.getRunFileDataObj(runNumber, contextName);

        dataFilePath = None
        if dataFile:
            dataFilePath = dataFile.dataFilePath

        return dataFilePath

    def getRunFileDataObj(self, runNumber, contextName):
        try:
            dataFile = self.session.query(DataFile).\
                filter(DataFile.run.has(runNumber=runNumber)).\
                filter(DataFile.contexts.any(contextName=contextName)).first()

            return dataFile
        except:
            self.rollback()
            raise

    def getRunFileDataWithProcPass(self, runNumber, contextName, processingPass):
        dataFile = self.getRunFileDataWithProcPassObj(runNumber, contextName, processingPass);

        dataFilePath = None
        if dataFile:
            dataFilePath = dataFile.dataFilePath

        return dataFilePath

    def getRunFileDataWithProcPassObj(self, runNumber, contextName, processingPass):
        try:
            dataFile = self.session.query(DataFile).\
                filter(DataFile.run.has(runNumber=runNumber)).\
                filter(DataFile.contexts.any(contextName=contextName)).\
                filter(DataFile.procPass.any(processingPass=processingPass)).first()

            return dataFile
        except:
            self.rollback()
            raise

    def getRunFileRef(self, runNumber, contextName):
        try:
            refFilePath = None

            refFile = self.session.query(ReferenceFile).\
                filter(ReferenceFile.runs.any(runNumber=runNumber)).\
                filter(ReferenceFile.contexts.any(contextName=contextName)).first()

            if refFile:
                refFilePath = refFile.refFilePath

            return refFilePath
        except:
            self.rollback()
            raise

    def getRunFileRefWithProcPass(self, runNumber, contextName, processingPass):
        try:
            refFilePath = None

            refFile = self.session.query(ReferenceFile).                    \
                filter(ReferenceFile.runs.any(runNumber=runNumber)).        \
                filter(ReferenceFile.contexts.any(contextName=contextName)).\
                filter(ReferenceFile.procPass.any(processingPass=processingPass)).\
                order_by(ReferenceFile.refFileId).first()

            if refFile:
                refFilePath = refFile.refFilePath

            return refFilePath
        except:
            self.rollback()
            raise
        
    def getRunFilesData(self, runNumber, contextName):
        try:
            filelist = []
            for dataFile in self.session.query(DataFile).\
                    filter(DataFile.run.has(runNumber=runNumber)).\
                    filter(DataFile.contexts.any(contextName=contextName)):
                filelist.append(dataFile.dataFilePath)

            return filelist
        except:
            self.rollback()
            raise

    def getRunFilesDataWithProcPass(self, runNumber, contextName, processingPass):
        try:
            filelist = []
            for dataFile in self.session.query(DataFile).\
                    filter(DataFile.run.has(runNumber=runNumber)).\
                    filter(DataFile.contexts.any(contextName=contextName)).\
                    filter(DataFile.procPass.any(processingPass=processingPass)):
                filelist.append(dataFile.dataFilePath)

            return filelist
        except:
            self.rollback()
            raise


    def getRunFilesRef(self, runNumber, contextName):
        try:
            filelist = []

            for refFile in self.session.query(ReferenceFile).\
                    filter(ReferenceFile.runs.any(runNumber=runNumber)).\
                    filter(ReferenceFile.contexts.any(contextName=contextName)):
                filelist.append(refFile.refFilePath)

            return filelist
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def getRunPropertyValue(self, propertyName, runNumber):
        try:
            value = None

            propertyId = self.getDataPropertyId(propertyName)
            if propertyId is None:
                return value

            s = run_data_property.select()
            s = s.where(run_data_property.c.runNumber==runNumber)
            s = s.where(run_data_property.c.dataPropertyId==propertyId)

            res = self.session.execute(s)
            for row in res:
                value = row[2]

            return value
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def getRunsPropertyValue(self, propertyName, runLow=0, runHigh=99999999):
        try:
            values = []

            propertyId = self.getDataPropertyId(propertyName)
            if propertyId is None:
                return values

            s = run_data_property.select()
            s = s.where(run_data_property.c.runNumber>=runLow)
            s = s.where(run_data_property.c.runNumber<=runHigh)
            s = s.where(run_data_property.c.dataPropertyId==propertyId)
            s = s.order_by(run_data_property.c.runNumber)

            res = self.session.execute(s)
            for row in res:
                value = [row[0],row[2]]
                values.append(value)

            res.close()
            return values
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def getRunsPropertyValueWithErr(self, propertyName, runLow=0, runHigh=99999999, dqFlag='ANY'):
        retval = {'OK'     : 0,
                  'values' : {}}

        propertyId = self.getDataPropertyId(propertyName)
        if propertyId is None:
            retval['OK'] = 1
            return retval

        propertyErr   = propertyName + '_err'
        propertyErrId = self.getDataPropertyId(propertyErr)
        if propertyErr is None:
            retval['OK'] = 2
            return retval

        if dqFlag == 'ANY':
            s = run_data_property.select()
            s = s.where(run_data_property.c.runNumber>=runLow)
            s = s.where(run_data_property.c.runNumber<=runHigh)
            s = s.where(or_(run_data_property.c.dataPropertyId==propertyId,run_data_property.c.dataPropertyId==propertyErrId))
            s = s.order_by(run_data_property.c.runNumber)
            res = self.session.execute(s)
        else:
             res = self.session.query(run_data_property).join(Run).join(Run.dqFlag).    \
                        filter(run_data_property.c.runNumber>=runLow).                  \
                        filter(run_data_property.c.runNumber<=runHigh).                 \
                        filter(DQFlags.dqFlag == dqFlag).                               \
                        filter(or_(run_data_property.c.dataPropertyId==propertyId,      \
                                   run_data_property.c.dataPropertyId==propertyErrId)). \
                        order_by(run_data_property.c.runNumber)

        for row in res:
            runNumber = str(row[0])
            if runNumber not in retval['values']:
                retval['values'][runNumber] = [0,0]

            if row[1] == propertyId:
                retval['values'][runNumber][0] = row[2]
            elif row[1] == propertyErrId:
                retval['values'][runNumber][1] = row[2]

        if dqFlag == 'ANY':
            res.close()

        return retval

    def getRuns(self, runLow=0, runHigh=99999999):
        try:
            runs = []
            for row in self.session.query(Run).         \
                        filter(Run.runNumber>=runLow).  \
                        filter(Run.runNumber<=runHigh). \
                        order_by(Run.runNumber):
                nextRun = row.runNumber
                runs.append(row.runNumber)
            return runs
        except:
            self.rollback()
            raise

    def getRunsWithDQFlag(self, dqFlag, runLow=0, runHigh=99999999):
        try:
            runs = []
            for row in self.session.query(Run).join(Run.dqFlag). \
                        filter(Run.runNumber>=runLow).           \
                        filter(Run.runNumber<=runHigh).          \
                        filter(DQFlags.dqFlag == dqFlag).        \
                        order_by(Run.runNumber):
                nextRun = row.runNumber
                runs.append(row.runNumber)
            return runs
        except:
            self.rollback()
            raise
    def getSimConditions(self):
        try:
            simConditions = []
            q = self.session.query(SimCondition)
            for r in q:
                simConditions.append(r.simCondition)
            return simConditions
        except:
            self.rollback()
            raise
    def getSimProcessingPasses(self):
        try:
            procPass = []
            q = self.session.query(SimProcessingPass)
            for r in q:
                procPass.append(r.simProcessingPass)
            return procPass
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def insertContext(self, name, commit=False):
        try:
            context = self.session.query(Context).filter_by(contextName=name).first()

            if context:
                return context
            else:
                context = Context(contextName=name)
                self.session.add(context)
                if commit:
                    self.commit()
                return context
        except:
            self.rollback()
            raise
    def insertDataFile(self, path, commit=False):
        try:
            retval = {'Added'    : False,
                      'datafile' : None}
            dataFile = self.session.query(DataFile).filter_by(dataFilePath=path).first()

            if dataFile:
                retval['datafile'] = dataFile
                return retval
            else:
                dataFile = DataFile(dataFilePath=path)
                self.session.add(dataFile)
                if commit:
                    self.commit()

                retval['datafile'] = dataFile
                retval['Added']    = True

                return retval
        except:
            self.rollback()
            raise
    def insertDataProperty(self, dataPropertyName, commit=False):
        try:
            retval       = {'Added'        : False,
                            'dataProperty' : None}
            dataProperty = self.session.query(DataProperty).filter_by(dataProperty=dataPropertyName).first()

            if dataProperty:
                retval['dataProperty'] = dataProperty
                return retval
            else:
                dataProperty = DataProperty(dataProperty=dataPropertyName)
                self.session.add(dataProperty)
                if commit:
                    self.commit()

                retval['dataProperty'] = dataProperty
                retval['Added']        = True

                return retval
        except:
            self.rollback()
            raise
    def insertDQFlag(self, flag, commit=False):
        try:
            retval = {'Added'  : False,
                      'dqFlag' : None}

            dqFlag = self.session.query(DQFlags).filter_by(dqFlag=flag).first()

            if dqFlag:
                retval['dqFlag'] = dqFlag
                return retval
            else:
                dqFlag = DQFlags(dqFlag=flag)
                self.session.add(dqFlag)
                if commit:
                    self.commit()

                retval['dqFlag'] = dqFlag
                retval['Added']  = True

                return retval
        except:
            self.rollback()
            raise
    def insertEventType(self, eventType, commit=False):
        try:
            if type(eventType) is str:
                eventType = int(eventType)

            eType = self.session.query(EventType).filter_by(eventType=eventType).first()

            if eType:
                return eType
            else:
                eType = EventType(eventType=eventType)
                self.session.add(eType)
                if commit:
                    self.commit()
                return eType
        except:
            self.rollback()
            raise
    def insertFill(self, fillId, commit=False):
        try:
            fill = self.session.query(Fill).filter_by(id=fillId).first()

            if fill:
                return fill
            else:
                fill = Fill(id=fillId)
                self.session.add(fill)
                if commit:
                    self.commit()
                return fill
        except:
            self.rollback()
            raise
    def insertProcessingPass(self, processingPassPath, commit=False):
        try:
            retval       = {'Added'          : False,
                            'processingPass' : None}
            processingPass = self.session.query(ProcessingPass).filter_by(processingPass=processingPassPath).first()

            if processingPass:
                retval['processingPass'] = processingPass
                return retval
            else:
                processingPass = ProcessingPass(processingPass=processingPassPath)
                self.session.add(processingPass)
                if commit:
                    self.commit()

                retval['processingPass'] = processingPass
                retval['Added']          = True

                return retval
        except:
            self.rollback()
            raise
    def insertRefFile(self, path, commit=False):
        try:
            retval = {'Added'    : False,
                      'refFile' : None}

            refFile = self.session.query(ReferenceFile).filter_by(refFilePath=path).first()

            if refFile:
                retval['refFile'] = refFile
                return retval
            else:
                refFile = ReferenceFile(refFilePath=path)
                self.session.add(refFile)

                retval['refFile'] = refFile
                retval['Added']   = True

                return retval
        except:
            self.rollback()
            raise
    def insertRun(self, runNumber, fillId, commit=False):
        try:
            run = self.getRun(runNumber)

            if run:
                return run
            else:
                fill = self.insertFill(fillId)
                run  = Run(runNumber=runNumber, fillId=fillId)
                self.session.add(run)
                if commit:
                    self.commit()

                return run
        except:
            self.rollback()
            raise
    def insertSimCondition(self, simCondition, commit=False):
        try:
            retval = {'Added'        : False,
                      'simCondition' : None}
            s      = self.session.query(SimCondition).filter_by(simCondition=simCondition).first()

            if s:
                retval['simCondition'] = s
                return retval
            else:
                s = SimCondition(simCondition=simCondition)
                self.session.add(s)
                if commit:
                    self.commit()

                retval['simCondition'] = s
                retval['Added']        = True

                return retval
        except:
            self.rollback()
            raise        
    def insertSimProcessingPass(self, simProcessingPassPath, commit=False):
        try:
            retval            = {'Added'             : False,
                                 'simProcessingPass' : None}
            simProcessingPass = self.session.query(SimProcessingPass).filter_by(simProcessingPass=simProcessingPassPath).first()

            if simProcessingPass:
                retval['simProcessingPass'] = simProcessingPass
                return retval
            else:
                simProcessingPass = SimProcessingPass(simProcessingPass=simProcessingPassPath)
                self.session.add(simProcessingPass)
                if commit:
                    self.commit()

                retval['simProcessingPass'] = simProcessingPass
                retval['Added']             = True

                return retval
        except:
            self.rollback()
            raise        
#------------------------------------------------------------------------------------
    def listTables(self):
        try:
            tables = list(self.base.metadata.tables.keys())
            print(tables)
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def nextOnlineDQRun(self, runNumber):
        try:
            nextRun = None
            for row in self.session.query(Run).         \
                        filter(Run.runNumber>runNumber).\
                        order_by(Run.runNumber).limit(1):
                nextRun = row.runNumber
            return nextRun
        except:
            self.rollback()
            raise
    def nextOnlineDQRunUnchecked(self, runNumber):
        try:
            nextRun = None
            for row in self.session.query(Run).join(Run.dqFlag). \
                        filter(Run.runNumber>runNumber).         \
                        filter(DQFlags.dqFlag == 'UNCHECKED').   \
                        order_by(Run.runNumber).limit(1):
                nextRun = row.runNumber
            return nextRun
        except:
            self.rollback()
            raise
    def nextOnlineDQRunUnknown(self, runNumber):
        try:
            nextRun = None
            for row in self.session.query(Run).join(Run.dqFlag). \
                        filter(Run.runNumber>runNumber).         \
                        filter(DQFlags.dqFlag == 'UNKNOWN').   \
                        order_by(Run.runNumber).limit(1):
                nextRun = row.runNumber
            return nextRun
        except:
            self.rollback()
            raise
    def prevOnlineDQRun(self, runNumber):
        try:
            prevRun = None
            for row in self.session.query(Run).              \
                            filter(Run.runNumber<runNumber). \
                            order_by(desc(Run.runNumber)).limit(1):
                prevRun = row.runNumber
            return prevRun
        except:
            self.rollback()
            raise
    def prevOnlineDQRunUnchecked(self, runNumber):
        try:
            nextRun = None
            for row in self.session.query(Run).join(Run.dqFlag). \
                        filter(Run.runNumber<runNumber).         \
                        filter(DQFlags.dqFlag == 'UNCHECKED').   \
                        order_by(desc(Run.runNumber)).limit(1):
                nextRun = row.runNumber
            return nextRun
        except:
            self.rollback()
            raise
    def prevOnlineDQRunUnknown(self, runNumber):
        try:
            nextRun = None
            for row in self.session.query(Run).join(Run.dqFlag). \
                        filter(Run.runNumber<runNumber).         \
                        filter(DQFlags.dqFlag == 'UNKNOWN').   \
                        order_by(desc(Run.runNumber)).limit(1):
                nextRun = row.runNumber
            return nextRun
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def rollback(self):
        self.session.rollback()
#------------------------------------------------------------------------------------
    def setRunDQFlag(self, run, flag, commit=False):
        try:
            retval = {'OK'       : True,
                      'Modified' : True}

            if type(run) is int:
                run = self.getRun(run)
            elif type(run) is str:
                run = self.getRun(int(run))

            if run is None:
                retval['OK'] = False
                return retval
            #
            # Get the DQ flag id number
            #

            dqFlagId = self.getDQFlagId(flag)

            if dqFlagId is None:
                retval['OK'] = False
                return retval

            stmt = 0
            if run.dqFlag is None:
                stmt = run_dq_flag.insert()
                stmt = stmt.values(runNumber=run.runNumber, dqFlagId=dqFlagId)
            else:
                if run.dqFlag.dqFlag == flag:
                    retval['Modified'] = False
                else:
                    stmt = run_dq_flag.update()
                    stmt = stmt.values(dqFlagId=dqFlagId)
                    stmt = stmt.where(run_dq_flag.c.runNumber==run.runNumber)

            if stmt != 0:
                self.session.execute(stmt)
                if commit:
                    self.commit()

            return retval
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def setFillPropertyValue(self, fill, name, value, commit=False):
        try:
            retval = {'OK'       : True,
                      'Modified' : True}

            if type(fill) is int:
                fill = self.getFill(fill)
            elif type(fill) is str:
                fill = self.getFill(int(fill))

            if fill is None:
                retval['OK'] = False
                return retval

            propertyId = self.getDataPropertyId(name)
            if propertyId is None:
                retval['OK'] = False
                return retval

            stmt = 0
            oldValue = self.getFillPropertyValue(name, fill.id)
            if oldValue is None:
                stmt = fill_data_property.insert()
                stmt = stmt.values(fillId=fill.id,dataPropertyId=propertyId,dataPropertyValue=value)
            else:
                if value == oldValue:
                    retval['Modified'] = False
                else:
                    stmt = fill_data_property.update()
                    stmt = stmt.values(dataPropertyValue=value)
                    stmt = stmt.where(fill_data_property.c.fillId==fill.id)
                    stmt = stmt.where(fill_data_property.c.dataPropertyId==propertyId)
            if stmt != 0:
                self.session.execute(stmt)
                if commit:
                    self.commit()
            return retval
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def setRunPropertyValue(self, run, name, value, commit=False):
        try:
            retval = {'OK'       : True,
                      'Modified' : True}

            if type(run) is int:
                run = self.getRun(run)
            elif type(run) is str:
                run = self.getRun(int(run))

            if run is None:
                retval['OK'] = False
                return retval

            propertyId = self.getDataPropertyId(name)
            if propertyId is None:
                retval['OK'] = False
                return retval

            stmt = 0
            oldValue = self.getRunPropertyValue(name, run.runNumber)
            if oldValue is None:
                stmt = run_data_property.insert()
                stmt = stmt.values(runNumber=run.runNumber,dataPropertyId=propertyId,dataPropertyValue=value)
            else:
                if value == oldValue:
                    retval['Modified'] = False
                else:
                    stmt = run_data_property.update()
                    stmt = stmt.values(dataPropertyValue=value)
                    stmt = stmt.where(run_data_property.c.runNumber==run.runNumber)
                    stmt = stmt.where(run_data_property.c.dataPropertyId==propertyId)
            if stmt != 0:
                self.session.execute(stmt)
                if commit:
                    self.commit()

            return retval
        except:
            self.rollback()
            raise
#------------------------------------------------------------------------------------
    def updateOfflineDQDataFile(self, run, processingPass, path, commit=False):
        try:
            retval = {'OK'      : True,
                      'Updated' : True} 

            if type(run) is int:
                run = self.getRun(run)
            elif type(run) is str:
                run = self.getRun(int(run))

            if run is None:
                retval['OK'] = False
                return retval

            oldDataFile = self.getRunFileDataWithProcPassObj(run.runNumber, self.offlineDQContextName, processingPass)

            ins         = self.insertDataFile(path)
            newDataFile = ins['datafile']

            if ins['Added']:
                self.commit()

            u = run_data_file.update()
            u = u.values(dataFileId=newDataFile.dataFileId)
            u = u.where(run_data_file.c.runNumber==run.runNumber)
            u = u.where(run_data_file.c.dataFileId==oldDataFile.dataFileId)

            self.session.execute(u)
            if commit:
                self.commit()
            return retval
        except:
            self.rollback()
            raise
        
    def updateOfflineDQRefFileForProcPass(self, processingPass, oldPath, newPath, commit=False):
      oldReference = self.getOfflineDQRefForProcPass(processingPass)

      oldRefFileId = -1
      for row in oldReference:
          if row.refFilePath == oldPath:
              oldRefFileId = row.refFileId
              break
      
      if oldRefFileId < 0:
          return None

      newReference = self.addOfflineDQRefFileWithProcPass(processingPass, newPath)
      if newReference is None:
          return None

      try: 
          u = run_ref_file.update()
          u = u.values(refFileId=newReference.refFileId)
          u = u.where(run_ref_file.c.refFileId==oldRefFileId)

          self.session.execute(u)
          if commit:
              self.commit()

          return True
      except:
          self.rollback()
          raise

    def updateOnlineDQDataFile(self, run, path, commit=False):
        try:
            oldDataFile = self.getRunFileDataObj(run.runNumber, self.onlineDQContextName)
            newDataFile = self.addOnlineDQFile(path)

            u = run_data_file.update()
            u = u.values(dataFileId=newDataFile.dataFileId)
            u = u.where(run_data_file.c.runNumber==run.runNumber)
            u = u.where(run_data_file.c.dataFileId==oldDataFile.dataFileId)

            self.session.execute(u)
            if commit:
                self.commit()
        except:
            self.rollback()
            raise

    def updateOnlineDQRef(self, run, refPath, commit=False):
        try:
            refFile   = self.addOnlineDQRefFile(run, refPath)
            contextId = self.getContextId('OnlineDQ')

            u = run_ref_file.update()
            u = u.values(refFileId=refFile.refFileId)
            u = u.where(run_ref_file.c.runNumber==run.runNumber)

            self.session.execute(u)
            if commit:
                self.commit()
        except:
            self.rollback()
            raise
