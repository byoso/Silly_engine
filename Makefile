generate_html_docs:
	madoc documentation/silly_orm_doc -t "Silly ORM" --code -o documentation/silly_orm_doc && \
	mv documentation/silly_orm_doc/documentation.madoc.html documentation/silly_orm_doc/Silly_orm_docs.html
	madoc documentation/data_validation_doc -t "Silly Engine - data_validation" --code -o documentation/data_validation_doc && \
	mv documentation/data_validation_doc/documentation.madoc.html documentation/data_validation_doc/Data_validation_docs.html
	madoc documentation/jsondb_doc -t "Silly Engine - jsondb" --code -o documentation/jsondb_doc && \
	mv documentation/jsondb_doc/documentation.madoc.html documentation/jsondb_doc/Jsondb_docs.html
	madoc documentation/logger_doc -t "Silly Engine - logger" --code -o documentation/logger_doc && \
	mv documentation/logger_doc/documentation.madoc.html documentation/logger_doc/Logger_docs.html
	madoc documentation/minuit_doc -t "Silly Engine - minuit" --code -o documentation/minuit_doc && \
	mv documentation/minuit_doc/documentation.madoc.html documentation/minuit_doc/Minuit_docs.html
	madoc documentation/router_doc -t "Silly Engine - router" --code -o documentation/router_doc && \
	mv documentation/router_doc/documentation.madoc.html documentation/router_doc/Router_docs.html
	madoc documentation/text_tools_doc -t "Silly Engine - text_tools" --code -o documentation/text_tools_doc && \
	mv documentation/text_tools_doc/documentation.madoc.html documentation/text_tools_doc/Text_tools_docs.html
	# rm madoc_sources.zip
	# rm madoc_build.sh
	madoc-bb \
		-p documentation/silly_orm_doc/Silly_orm_docs.html \
		-p documentation/data_validation_doc/Data_validation_docs.html \
		-p documentation/jsondb_doc/Jsondb_docs.html \
		-p documentation/logger_doc/Logger_docs.html \
		-p documentation/minuit_doc/Minuit_docs.html \
		-p documentation/router_doc/Router_docs.html \
		-p documentation/text_tools_doc/Text_tools_docs.html \
		-o documentation -t "Silly Engine"
	mv documentation/madoc-bookbinding.html documentation/Silly_Engine_docs.html
