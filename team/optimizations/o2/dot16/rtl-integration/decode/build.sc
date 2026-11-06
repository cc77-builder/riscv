import mill._
import scalalib._

// This build contains only the original harness source and the read-only probe.
// Exported core classes/resources are supplied by the official runClasspath task.
val workspace = os.Path(sys.env("MILL_WORKSPACE_ROOT"))

object probe extends ScalaModule {
  override def scalaVersion = "2.13.15"
  override def sources = T.sources { Seq(PathRef(workspace / "src")) }
  def exportedClasspath = T.source { workspace / "classpath-paths.json" }
  override def unmanagedClasspath = T {
    val paths = ujson.read(os.read(exportedClasspath().path)).arr.map(x => PathRef(os.Path(x.str)))
    Agg.from(paths)
  }
  override def ivyDeps = super.ivyDeps() ++ Agg(ivy"org.chipsalliance::chisel:6.6.0")
  override def scalacPluginIvyDeps = super.scalacPluginIvyDeps() ++
    Agg(ivy"org.chipsalliance:::chisel-plugin:6.6.0")
  override def scalacOptions = super.scalacOptions() ++
    Agg("-language:reflectiveCalls", "-Ymacro-annotations", "-Ytasty-reader")
  override def forkArgs = Seq("-Xmx4G", "-Xss8m", "-XX:ActiveProcessorCount=1")
}
