LESSC = lessc
RM = rm
OUTPUT_DIR = ../css

LESS_FILES = $(wildcard *.less)
CSS_FILES = $(LESS_FILES:.less=.css)
CSS_OUTPUT_FILES = $(addprefix $(OUTPUT_DIR)/, $(CSS_FILES))

all: $(CSS_OUTPUT_FILES)

clean:
	$(RM) $(CSS_OUTPUT_FILES)

$(CSS_OUTPUT_FILES): $(LESS_FILES)
	$(LESSC) $< > $(OUTPUT_DIR)/$@
