import mill._, scalalib._

// Isolated arithmetic/flow prototype. The frozen production build is untouched.
object dot16 extends ScalaModule {
  def scalaVersion = "2.13.15"
  override def scalacOptions = super.scalacOptions() ++ Agg("-language:reflectiveCalls")
  override def ivyDeps = Agg(ivy"org.chipsalliance::chisel:6.6.0")
  override def scalacPluginIvyDeps = Agg(ivy"org.chipsalliance:::chisel-plugin:6.6.0")
  override def sources = T.sources {
    val sourceRoot = os.Path(sys.env("DOT16_SOURCE_ROOT"))
    Seq(PathRef(sourceRoot / "Dot16.scala"),
        PathRef(os.Path(sys.env("DOT16_PARAM_SOURCE"))))
  }
}
