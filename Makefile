generate_html_docs:
	madoc documentation/silly_orm_doc -t "Silly ORM" --code -o documentation/silly_orm_doc && \
	mv documentation/silly_orm_doc/documentation.madoc.html documentation/silly_orm_doc/Silly_orm_docs.html
	# rm madoc_sources.zip
	# rm madoc_build.sh
	madoc-bb -p documentation/silly_orm_doc/Silly_orm_docs.html -o documentation -t "Silly Engine"
	mv documentation/madoc-bookbinding.html documentation/Silly_Engine_docs.html
