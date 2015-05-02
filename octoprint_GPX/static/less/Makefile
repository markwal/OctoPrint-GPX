LESSC = lessc
RM = rm
OUTPUT_DIR = ../css

LESS_FILES = $(wildcard *.less)
CSS_FILES = $(LESS_FILES:.less=.css)
CSS_OUTPUT_FILES = $(addprefix $(OUTPUT_DIR)/, $(CSS_FILES))

all: $(CSS_FILES)

clean:
	$(RM) $(CSS_OUTPUT_FILES)

%.css: %.less
	$(LESSC) $< > $(OUTPUT_DIR)/$@
