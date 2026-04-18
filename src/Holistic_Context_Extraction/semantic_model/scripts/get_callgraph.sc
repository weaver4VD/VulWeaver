import io.shiftleft.semanticcpg.language.*
import scala.collection.mutable
import upickle.default._
import ujson._

@main def exec(cpgFile: String, output: String): Unit = {
  importCpg(cpgFile)

  val callGraphMap = mutable.LinkedHashMap.empty[String, ujson.Value]

  val methods = cpg.method.l
  var i = 0
  val total = methods.size

  methods.foreach { m =>
    val callsJsonStr = m.call.toJson
    val callsJson    = ujson.read(callsJsonStr)
    callGraphMap += (m.id.toString -> callsJson)

    i += 1
    if (i % 100 == 0 || i == total) println(s"processed $i / $total methods")
  }

  val outJson = ujson.Obj.from(callGraphMap.toSeq)
  val pretty  = outJson.render(2)

  import os._
  os.write.over(os.Path(output, os.pwd), pretty)
}