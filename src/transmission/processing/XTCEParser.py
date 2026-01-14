from py4j.java_gateway import launch_gateway
from py4j.java_gateway import JavaGateway
from py4j.protocol import Py4JJavaError
from django_logger import logger


# pylint: disable=all
class XTCEParser:
    gateway_started = 0

    def __init__(self, XTCEfile, stream):
        #logger.info("XTCETools " + str(XTCEfile) + " " + str(XTCEParser.gateway_started))
        #if XTCEParser.gateway_started == 0:
        #    XTCEParser.gateway_started = 1
        #    logger.info("Loading XTCETools")
        #    launch_gateway(classpath='transmission/processing/xtcetools-1.1.5.jar',
        #                   port=25333,
        #                   die_on_exit=True)

        logger.info("Loading XTCEParser")
        gateway = JavaGateway()

        XTCEContainerContentModel = gateway.jvm.org.xtce.toolkit.XTCEContainerContentModel
        XTCEContainerEntryValue = gateway.jvm.org.xtce.toolkit.XTCEContainerEntryValue
        XTCEDatabase = gateway.jvm.org.xtce.toolkit.XTCEDatabase
        XTCEDatabaseException = gateway.jvm.org.xtce.toolkit.XTCEDatabaseException
        XTCEParameter = gateway.jvm.org.xtce.toolkit.XTCEParameter
        XTCETMStream = gateway.jvm.org.xtce.toolkit.XTCETMStream
        XTCEValidRange = gateway.jvm.org.xtce.toolkit.XTCEValidRange
        XTCEContainer = gateway.jvm.org.xtce.toolkit.XTCETMContainer
        XTCEEngineeringType = gateway.jvm.org.xtce.toolkit.XTCETypedObject.EngineeringType
        File = gateway.jvm.java.io.File

        self.XTCEfile_ = XTCEfile
        self.db_ = XTCEDatabase(File(XTCEfile), True, False, True)
        self.stream_ = self.db_.getStream(stream)

    def loadGateway():
        logger.info("Loading py4j and XTCETools")
        launch_gateway(classpath='transmission/processing/xtcetools-1.1.5.jar',
                        port=25333,
                        die_on_exit=True)

    def getFile(self):
        return self.XTCEfile

    def processTMFrame(self, data):
        try:
            model = self.stream_.processStream(data)
            entries = model.getContentList()
            telemetry = {"frame": model.getName()}

            # throw an error if the frame is found but empty
            for entry in entries:
                val = entry.getValue()
                name = entry.getName()

                if val and entry.getParameter().getAncillaryData("Ignore").isEmpty():
                    telemetry[name] = {"value": val.getCalibratedValue(), "status": self.isFieldValid(entry)}

            return telemetry
        except Py4JJavaError as ex:
            raise XTCEException(ex.java_exception)

    def isFieldValid(self, entry):
        param = entry.getParameter()

        if not param:
            return "Valid"

        rang = param.getValidRange()

        if not rang.isValidRangeApplied():
            return "Valid"
        else:

            if rang.isLowValueCalibrated():
                valLow = entry.getValue().getCalibratedValue()
            else:
                valLow = entry.getValue().getUncalibratedValue()

            if rang.isLowValueInclusive():
                if float(valLow) < float(rang.getLowValue()):
                    return "Too Low"
            else:
                if float(valLow) <= float(rang.getLowValue()):
                    return "Too Low"

            if rang.isHighValueCalibrated():
                valHigh = entry.getValue().getCalibratedValue()
            else:
                valHigh = entry.getValue().getUncalibratedValue()

            if rang.isHighValueInclusive():
                if float(valHigh) > float(rang.getHighValue()):
                    return "Too High"
            else:
                if float(valHigh) >= float(rang.getHighValue()):
                    return "Too High"

            # the valid range is not recognized but the value is anyway valid
            return "Valid"


class XTCEException(Exception):
    """Exception raised by xtcetools.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


class SatParsers:

    def __init__(self):
        self.parsers = {
            "delfi_pq": XTCEParser("delfipq/Delfi-PQ.xml", "Radio"),
            #"delfi_next": None,
            "delfi_c3": XTCEParser("delfic3/Delfi-C3.xml", "TLM"),
            #"da_vinci": None
        }
