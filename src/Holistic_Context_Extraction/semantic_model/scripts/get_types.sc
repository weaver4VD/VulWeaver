@main def exec(cpgFile: String, output: String): Unit = {
  importCpg(cpgFile);
   cpg.typeDecl.toJson |> s"${output}" 
}