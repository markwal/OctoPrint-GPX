SUBDIRS = GPX/build octoprint_GPX/static/less

.PHONY: all clean test machines

all: GPX/build
	for dir in $(SUBDIRS); do \
		echo "Entering $$dir"; \
		make -C $$dir $@; \
		echo "Exiting $$dir"; \
	done
	python setup.py develop

GPX/build: GPX/configure
	mkdir -p GPX/build
	cd GPX/build ; ../configure ; cd ../..

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
