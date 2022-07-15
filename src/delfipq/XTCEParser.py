from py4j.java_gateway import launch_gateway
from py4j.java_gateway import JavaGateway
from py4j.protocol import Py4JJavaError
# pylint: disable=all
class XTCEParser:
  def __init__(self, XTCEfile, stream):
    launch_gateway(classpath='src/delfipq/xtcetools-1.1.5.jar',
			   port=25333,
			   die_on_exit=True)

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

    self.db_ = XTCEDatabase(File(XTCEfile), True, False, True)
    self.stream_ = self.db_.getStream(stream)

  def processTMFrame(self, data):
     try:
        model = self.stream_.processStream(data)
        entries = model.getContentList()
        telemetry = {"frame": model.getName()}

        for entry in entries:
            val = entry.getValue()
            name = entry.getName()

            if val:
                telemetry[name] = val.getCalibratedValue()

        return telemetry
     except Py4JJavaError as ex:
        raise XTCEException(str(ex)) from ex

class XTCEException(Exception):
    """Exception raised by xtcetools.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)