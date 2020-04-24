# DataSync - MySQL+MongoDB -> WordPress


# Usage

 - Setup a Virtual Environment
 - Set the "config.ini" file based on the "config.init.sample".
 - Execute "report.py"

### Activate virtual environment and install its dependencies
```bash
virtualenv venv --python=python3
source venv/bin/activate
python -m pip install -r requirements.txt --upgrade
```

### Set the "config.ini" file based on the "config.init.sample".
```bash
cp config.sample.yml config.yml
vi config.yml
```

### Execute "sync.py"
```bash
python sync.py
```
#### Opções ####
```bash
python sync.py [-t] [-c|--config <config.yml>] [-d|--debug <level>] [-i|--course <course-id>] -e|environment <environment>
```

 * -e --environment <environment>
    * define o ambiente destino: "stage" ou "prod" 
 * -d --debug <debug level>
    * re-define o nível de logging: DEBUG, INFO, WARNING, CRITICAL, FATAL 
 * -c --config <config file>
    * ficheiro de configuração. Por omissão, config.yml na pasta atual
 * -i --course <course-id>
    * identifica um curso único para atualizar
 * -t
    * modo de teste - não aplica modificações no wordpress destino

### Informação Adicional ###

Estrutura de acesso MongoDB do OpenEDX.

Conceitos:
1. A collection “active_versions” tem os cursos ativos no momento
1. A collection “structures” tem os cursos em histórico
1. A collection “definitions” tem os objetos propriamente ditos

O passo de pesquisa é sempre:
 -	Um curso é definido por:
      - Course
      - Org
      - run
 -	Encontrar o curso em “active_versions”.
 -	Seleccionar o “published-branch”
      -	Iterar pelos “blocks”
      - O “block_type” indica que tipo de bloco é
      - O “definition” indica qual o objeto em “definitions” que tem este conteúdo
      - Finalmente é preciso consultar a collection “definitions” pesquisando pelo “_id” do objeto referenciado por block[“definition”]
 
Este é um script mongodb que lista todos os objetos a colocar no Wordpress!
 
    db.modulestore.active_versions.find({"course":"IPLR02", "org":"IPLeiria", "run":"I2019"}).forEach(
        function(obj) {        
            var published_id = obj["versions"]["published-branch"];
            struct_obj = db.modulestore.structures.find(published_id).forEach(
              function(obj) {
                  obj["blocks"].forEach(
                    function(block) {
                        if(block["block_type"]=="about") {
                            print( {
                                "block_id": block["block_id"],
                                //"edited_on": block["edit_info"]["edited_on"],
                                // "content_id": block["edit_info"]["source_version"],
                                "content": db.modulestore.definitions.findOne({"_id" : block["definition"]})["fields"]["data"],
                                // "block": block
                            } );
                        }
                    }
                  );
              }
            );
        }
    )
 
O resultado é o seguinte:
 
    /* 1 */
    {
        "block_id" : "effort",
        "content" : "2 h/semana"
    }
     
    /* 2 */
    {
        "block_id" : "duration",
        "content" : ""
    }
     
    /* 3 */
    {
        "block_id" : "title",
        "content" : ""
    }
     
    /* 4 */
    {
        "block_id" : "about_sidebar_html",
        "content" : ""
    }
     
    /* 5 */
    {
        "block_id" : "short_description",
        "content" : "Este curso aborda, de forma introdutória, as normas de acessibilidade web e as estratégias para tornar acessíveis os formatos de conteúdo mais utilizados na web."
    }
     
    /* 6 */
    {
        "block_id" : "entrance_exam_id",
        "content" : ""
    }
     
    /* 7 */
    {
        "block_id" : "entrance_exam_minimum_score_pct",
        "content" : "50"
    }
     
    /* 8 */
    {
        "block_id" : "subtitle",
        "content" : ""
    }
     
    /* 9 */
    {
        "block_id" : "overview",
        "content" : "<section class=\"about\">\n  <h2>Sobre o curso</h2>\n  <p>O curso começa com uma introdução à regulamentação da acessibilidade web, fornecendo uma perspetiva histórica, quer no panorama mundial, quer em Portugal, e uma clarificação das diretrizes de acessibilidade para conteúdo web (WCAG). Segue-se o módulo que introduz a questão das interfaces, dos produtos ou tecnologias de apoio e as ferramentas para verificar o nível de conformidade com as WCAG 2.0 das páginas web. Os módulos seguintes abordam as estratégias para criar e disponibilizar conteúdo acessível nas páginas web, ou seja, imagem, texto e vídeo.</p>\n <p>Em cada módulo são apresentados desafios que permitem ao participante avaliar o seu nível de aprendizagem e refletir sobre o tema abordado em cada módulo.</p>\n <p>Os conteúdos e atividades propostas são acessíveis a tecnologias de apoio, permitindo a qualquer utilizador participar no curso.</p>\n  <p></p>\n  <h2>Contactos</h2>\n  <p>E-mail: suporte.ued@ipleiria.pt.</p>\n  <p>Tel: (351) 244845052</p>\n</section>\n\n<section class=\"prerequisites\">\n  <h2>Pré-requisitos</h2>\n  <p>Este curso destina-se a qualquer pessoa que contribua com conteúdos para a web (em sites, redes sociais, blogs, email, etc.) ou com interesse na temática, sendo por isso fundamental estar familiarizado com o ambiente web.</p>\n</section>\n\n<section class=\"course-staff\">\n  <h2>Instrutores</h2>\n  <article class=\"teacher\">\n    <div class=\"teacher-image\" style=\"border:none;\">\n      <img src=\"/static/foto_manuela_francisco.png\" align=\"left\" style=\"margin:0 20 px 0\" alt=\"Foto de Manuela Francisco\">\n    </div>\n\n    <h3>Manuela Francisco</h3>\n    <p style=\"padding-left:131px;\">Doutorada em Educação a Distancia e eLearning, desenvolve investigação na área do eLearning acessível. É Designer Instrucional no Politécnico de Leiria, desde 2007. Foi docente na ESAD-FRESS e colabora com a Universidade Aberta em atividades de investigação e docência. Integra a equipa de revisão da versão portuguesa das WCAG e esteve envolvida em vários projetos europeus e grupos de trabalho nacionais.</p>\n  </article>\n  \n  <article class=\"teacher\">\n    <div class=\"teacher-image\" style=\"border:none;\">\n      <img src=\"/static/foto_sandro_costa.png\" align=\"left\" style=\"margin:0 20 px 0\" alt=\"Foto de Sabdro Costa\">\n    </div>\n\n    <h3>Sandro Costa</h3>\n    <p style=\"padding-left:131px;\">Licenciado em Comunicação e Multimedia e doutorando em Ciência e Tecnologia Web. Trabalha como Designer Multimedia na Unidade de Ensino a Distância do Politécnico de Leiria, desde 2008. Esteve envolvido em projetos europeus e nacionais como especialista multimédia. Ao nível da programação desenvolve sites, eBooks e plataformas acessíveis.</p>\n  </article>\n\n  <article class=\"teacher\">\n    <div class=\"teacher-image\" style=\"border:none;\">\n      <img src=\"/static/foto_formador_carina.jpg\" align=\"left\" style=\"margin:0 20 px 0\" alt=\"Foto de Carina Rodrigues\">\n    </div>\n\n    <h3>Carina Rodrigues</h3>\n    <p style=\"padding-left:131px;\">Mestre em Ciências da Educação na área de Educação de Adultos, a terminar o Doutoramento em Ensino a Distância e eLearning. É Designer Instrucional e formadora na Unidade de Ensino a Distância do Politécnico de Leiria, desde 2008. Esteve envolvida em projetos europeus e nacionais relacionados com a área da inovação social, competências digitais e estratégias de active learning, desenvolvendo investigação nestas áreas.</p>\n  </article>\n</section>\n\n"
    }
     
    /* 10 */
    {
        "block_id" : "entrance_exam_enabled",
        "content" : "false"
    }
     
    /* 11 */
    {
        "block_id" : "description",
        "content" : ""
    }
