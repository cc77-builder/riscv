// Compile the production source in isolation with the active root build.sc pins.
scalaVersion := "2.13.15"
libraryDependencies ++= Seq(
  "org.chipsalliance" %% "chisel" % "6.6.0",
  "edu.berkeley.cs" %% "chiseltest" % "6.0.0" % Test,
  "org.scalatest" %% "scalatest" % "3.2.19" % Test
)
addCompilerPlugin("org.chipsalliance" % "chisel-plugin" % "6.6.0" cross CrossVersion.full)
Compile / unmanagedSources += baseDirectory.value / "../../../src/main/scala/xiangshan/backend/fu/vector/VdotExec.scala"
Test / parallelExecution := false
scalacOptions ++= Seq("-deprecation", "-feature", "-unchecked", "-language:reflectiveCalls")
