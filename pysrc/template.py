mainhtml_temp = """Content-type: text/html\n\n
<html lang="en">
<head>
<meta charset="utf-8">
<title>DKMS New Allele Submitter</title>
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap-theme.min.css">
<script type="text/javascript" src="https://code.jquery.com/jquery-1.11.2.min.js"></script>
<script type="text/javascript" src="http://192.168.2.159/typeloader/bootstrap/js/bootstrap.min.js"></script>

</head>
<body>
    <nav id="myNavbar" class="navbar navbar-default navbar-inverse navbar-fixed-top" role="navigation">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="container">
            <div class="navbar-header">
                <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#navbarCollapse">
                    <span class="sr-only">Toggle navigation</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </button>
                <a class="navbar-brand" href="http://192.168.2.159/typeloader/index.html">TypeLoader</a>
            </div>
            <!-- Collect the nav links, forms, and other content for toggling -->
            <div class="collapse navbar-collapse" id="navbarCollapse">
                <ul class="nav navbar-nav">
                    <li class="active"><a href="http://192.168.2.159/typeloader/index.html">Home</a></li>
                    <li><a href="" target="_blank">About</a></li>
                    <li><a href="" target="_blank">Contact</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        <div class="jumbotron">
            <h4>%s</h4>
            <h3>ENA</h3>
            <pre>%s</pre>
            <h3>IMGT</h3>
            <pre>%s</pre>
            <p><a href="http://192.168.2.159/downloads/enafiles/%s" class="btn btn-success" download>Download ENA File &raquo;</a></p>
            <p><a href="http://192.168.2.159/downloads/imgtfiles/%s" class="btn btn-success" download>Download IMGT File &raquo;</a></p>
        </div>
    </div>
    <div class="row">
            <div class="col-xs-12">
                <footer>
                    <p>&copy; Copyright 2015 DKMS Life Sciences Lab</p>
                </footer>
            </div>
        </div>
    </div>
</body>
</html>"""

mainhtml = """Content-type: text/html\n\n
<html lang="en">
<head>
<meta charset="utf-8">
<title>DKMS New Allele Submitter</title>
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap-theme.min.css">
<script type="text/javascript" src="https://code.jquery.com/jquery-1.11.2.min.js"></script>
<script type="text/javascript" src="http://192.168.2.159/typeloader/bootstrap/js/bootstrap.min.js"></script>

</head>
<body>
    <nav id="myNavbar" class="navbar navbar-default navbar-inverse navbar-fixed-top" role="navigation">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="container">
            <div class="navbar-header">
                <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#navbarCollapse">
                    <span class="sr-only">Toggle navigation</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </button>
                <a class="navbar-brand" href="http://192.168.2.159/typeloader/index.html">TypeLoader</a>
            </div>
            <!-- Collect the nav links, forms, and other content for toggling -->
            <div class="collapse navbar-collapse" id="navbarCollapse">
                <ul class="nav navbar-nav">
                    <li class="active"><a href="http://192.168.2.159/typeloader/index.html">Home</a></li>
                    <li><a href="" target="_blank">About</a></li>
                    <li><a href="" target="_blank">Contact</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        <div class="jumbotron">
            <h4>%s</h4>
            <pre>%s</pre>
            <p><a href="http://192.168.2.159/downloads/enafiles/%s" class="btn btn-success" download>Download File &raquo;</a></p>
        </div>
    </div>
    <div class="row">
            <div class="col-xs-12">
                <footer>
                    <p>&copy; Copyright 2015 DKMS Life Sciences Lab</p>
                </footer>
            </div>
        </div>
    </div>
</body>
</html>"""

allelechooser = """Content-type: text/html\n\n
<html lang="en">
<head>
<meta charset="utf-8">
<title>DKMS New Allele Submitter</title>
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap-theme.min.css">
<script type="text/javascript" src="https://code.jquery.com/jquery-1.11.2.min.js"></script>
<script type="text/javascript" src="http://192.168.2.159/typeloader/bootstrap/js/bootstrap.min.js"></script>

</head>
<body>
    <nav id="myNavbar" class="navbar navbar-default navbar-inverse navbar-fixed-top" role="navigation">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="container">
            <div class="navbar-header">
                <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#navbarCollapse">
                    <span class="sr-only">Toggle navigation</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </button>
                <a class="navbar-brand" href="http://192.168.2.159/typeloader/index.html">TypeLoader</a>
            </div>
            <!-- Collect the nav links, forms, and other content for toggling -->
            <div class="collapse navbar-collapse" id="navbarCollapse">
                <ul class="nav navbar-nav">
                    <li class="active"><a href="http://192.168.2.159/typeloader/index.html">Home</a></li>
                    <li><a href="" target="_blank">About</a></li>
                    <li><a href="" target="_blank">Contact</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        <div class="jumbotron">
            
            <br>
            <form action='choose_allele.cgi' method='post' enctype='multipart/form-data'>
                <input type="hidden" name="xmlfilename" value="%s">
                <div class="input-group">
                    <input type="hidden" name="allele1name" value="%s">
                    <input type="hidden" name="allele1closest" value = "%s">
                    <span class="input-group-addon">
                        <input type="checkbox" name="allele1">
                    </span>
                    <input type="text" class="form-control" placeholder="GenDX : %s | ClosestAllele : %s" disabled="disabled">
                </div>
                <br>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#accordion" href="#collapseTwo">Enter Allele Details</a>
                        </h4>
                    </div>
                    <div id="collapseTwo" class="panel-collapse collapse">
                        <div class="panel-body">
                               
                                    <label for="genename">Name of gene</label>
                                    <input type="text" class="form-control" name="allele1_genename" placeholder="HLA-%s" value="HLA-%s">
                                
                                
                                    <label for="allelename">Name for the new allele</label>
                                    <input type="text" class="form-control" name="allele1_allelename" placeholder="%s" value="%s">
                                        
                                    <label for="product">Cell Line</label>
                                    <input type="text" class="form-control" name="allele1_cellline" placeholder="Cell line" value="">
                                
                                    <label for="product">Product</label>
                                    <input type="text" class="form-control" name="allele1_product" placeholder="%s" value="%s">
                               
                        </div>
                    </div>
                </div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#accordion" href="#collapseThree">Allele Specific Options</a>
                        </h4>
                    </div>
                    <div id="collapseThree" class="panel-collapse collapse">
                        <div class="panel-body">
                            <p>Exon subset option</p>
                            <div class="form-group">
                                    <label for="fromexon">From Exon</label>
                                    <input type="text" class="form-control" name="allele1_fromexon" placeholder="0" value="0">
                            </div>
                            <div class="form-group">
                                    <label for="product">To Exon</label>
                                    <input type="text" class="form-control" name="allele1_toexon" placeholder="0" value="0">
                            </div>
                        </div>
                    </div>
                </div>
                
                <br>
                <br>
                
                <div class="input-group">
                    <input type="hidden" name="allele2name" value="%s">
                    <input type="hidden" name="allele2closest" value="%s">
                    <span class="input-group-addon">
                        <input type="checkbox" name="allele2">
                    </span>
                    <input type="text" class="form-control" placeholder="GenDX : %s | ClosestAllele : %s" disabled="disabled">
                </div>
                <br>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#accordion" href="#collapseFour">Enter Allele Details</a>
                        </h4>
                    </div>
                    <div id="collapseFour" class="panel-collapse collapse">
                        <div class="panel-body">
                               
                                    <label for="genename">Name of gene</label>
                                    <input type="text" class="form-control" name="allele2_genename" placeholder="HLA-%s" value="HLA-%s">
                                
                                
                                    <label for="allelename">Name for the new allele</label>
                                    <input type="text" class="form-control" name="allele2_allelename" placeholder="%s" value="%s">
                                        
                                    <label for="product">Cell Line</label>
                                    <input type="text" class="form-control" name="allele2_cellline" placeholder="Cell line" value="">
                                
                                    <label for="product">Product</label>
                                    <input type="text" class="form-control" name="allele2_product" placeholder="%s" value="%s">
                               
                        </div>
                    </div>
                </div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#accordion" href="#collapseFive">Allele Specific Options</a>
                        </h4>
                    </div>
                    <div id="collapseFive" class="panel-collapse collapse">
                        <div class="panel-body">
                            <p>Exon subset option</p>
                            <div class="form-group">
                                    <label for="fromexon">From Exon</label>
                                    <input type="text" class="form-control" name="allele2_fromexon" placeholder="0" value="0">
                            </div>
                            <div class="form-group">
                                    <label for="product">To Exon</label>
                                    <input type="text" class="form-control" name="allele2_toexon" placeholder="0" value="0">
                            </div>
                        </div>
                    </div>
                </div>
                    
                
                <br>
                <br>
                
                <div class="input-group">
                   
                    <span class="input-group-addon">
                        <input type="checkbox" name="both">
                    </span>
                    <input type="text" class="form-control" placeholder="Both Alleles" disabled="disabled">
                </div>
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a data-toggle="collapse" data-parent="#accordion" href="#collapseThree">When selecting this option, please ensure you have entered details for both alleles</a>
                        </h4>
                    </div>
                </div>
                
                <br>
                <button type="submit" class="btn btn-primary">Process Choice</button>
            </form>
        </div>
    </div>
    <div class="row">
            <div class="col-xs-12">
                <footer>
                    <p>&copy; Copyright 2015 DKMS Life Sciences Lab</p>
                </footer>
            </div>
        </div>
    </div>
</body>
</html>"""

bulkdownload = """Content-type: text/html\n\n
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DKMS New Allele Submitter</title>
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap-theme.min.css">
<script type="text/javascript" src="https://code.jquery.com/jquery-1.11.2.min.js"></script>
<script type="text/javascript" src="http://192.168.2.159/typeloader/bootstrap/js/bootstrap.min.js"></script>

</head>
<body>
    <nav id="myNavbar" class="navbar navbar-default navbar-inverse navbar-fixed-top" role="navigation">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="container">
            <div class="navbar-header">
                <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#navbarCollapse">
                    <span class="sr-only">Toggle navigation</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </button>
                <a class="navbar-brand" href="#">TypeLoader</a>
            </div>
            <!-- Collect the nav links, forms, and other content for toggling -->
            <div class="collapse navbar-collapse" id="navbarCollapse">
                <ul class="nav navbar-nav">
                    <li class="active"><a href="http://192.168.2.159/typeloader/index.html">Home</a></li>
                    <li><a href="" target="_blank">About</a></li>
                    <li><a href="" target="_blank">Contact</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        
        <div class="jumbotron">
            
        <div class="panel-group" id="accordion">
        <form action='cgi-bin/blast.cgi' method='post' enctype='multipart/form-data'>
        <div class="panel panel-default">
            <div class="panel-heading">
                <h4 class="panel-title">
                    <a data-toggle="collapse" data-parent="#accordion" href="#collapseOne"></a>
                </h4>
            </div>
            <div id="collapseOne" class="panel-collapse collapse in">
                <div class="panel-body">
                    <p>Download collated ENA file</p>
                    <p><a href="http://192.168.2.159%s" class="btn btn-success" download>%s &raquo;</a></p>
                    
                           
                </div>
            </div>
        </div>
        
        <br>
            <br>
            
            </form>
    </div>
       
        </div>
         
    </div>
    <div class="row">
            <div class="col-xs-12">
                <footer>
                    <p>&copy; Copyright 2015 DKMS Life Sciences Lab</p>
                </footer>
            </div>
        </div>
    </div>
</body>
</html>"""

imgtdownload = """Content-type: text/html\n\n
<!DOCTYPE html>
<html lang="en">

<head>
<meta charset="utf-8">
<title>DKMS New Allele Submitter</title>
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="http://192.168.2.159/typeloader/bootstrap/css/bootstrap-theme.min.css">
<script type="text/javascript" src="https://code.jquery.com/jquery-1.11.2.min.js"></script>
<script type="text/javascript" src="http://192.168.2.159/typeloader/bootstrap/js/bootstrap.min.js"></script>
</head>

<body>
    <nav id="myNavbar" class="navbar navbar-default navbar-inverse navbar-fixed-top" role="navigation">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="container">
            <div class="navbar-header">
                <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#navbarCollapse">
                    <span class="sr-only">Toggle navigation</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </button>
                <a class="navbar-brand" href="#">TypeLoader</a>
            </div>
            <!-- Collect the nav links, forms, and other content for toggling -->
            <div class="collapse navbar-collapse" id="navbarCollapse">
                <ul class="nav navbar-nav">
                    <li class="active"><a href="http://192.168.2.159/typeloader/index.html">Home</a></li>
                    <li><a href="" target="_blank">About</a></li>
                    <li><a href="" target="_blank">Contact</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        
        <div class="jumbotron">
            
        <div class="panel-group" id="accordion">
        <form action='cgi-bin/blast.cgi' method='post' enctype='multipart/form-data'>
        <div class="panel panel-default">
            <div class="panel-heading">
                <h4 class="panel-title">
                    <a data-toggle="collapse" data-parent="#accordion" href="#collapseOne"></a>
                </h4>
            </div>
            <div id="collapseOne" class="panel-collapse collapse in">
                <div class="panel-body">
                    <p>Download a zipped folder containing IMGT files</p>
                    <p><a href="http://192.168.2.159%s" class="btn btn-success" download>%s &raquo;</a></p>
                    
                           
                </div>
            </div>
        </div>
        
        <br>
            <br>
            
            </form>
    </div>
       
        </div>
         
    </div>
    <div class="row">
            <div class="col-xs-12">
                <footer>
                    <p>&copy; Copyright 2015 DKMS Life Sciences Lab</p>
                </footer>
            </div>
        </div>
    </div>
</body>
</html>"""

