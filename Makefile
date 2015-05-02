SUBDIRS = GPX octoprint_GPX/static/less

.PHONY: all clean test machines

all:
	python setup.py develop
	for dir in $(SUBDIRS); do \
		echo "Entering $$dir"; \
		make -C $$dir $@; \
		echo "Exiting $$dir"; \
	done

clean:
	python setup.py clean
	for dir in $(SUBDIRS); do \
		make -C $$dir clean; \
	done

test:
	for dir in $(SUBDIRS); do \
		make -C $$dir $@; \
	done

less:
	make -C octoprint_GPX/static/less
