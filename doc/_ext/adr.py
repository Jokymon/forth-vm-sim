from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


class Adr(SphinxDirective):
    has_content = True
    option_spec = {
        'creation_date': directives.unchanged_required,
        'last_update': directives.unchanged_required,
        'status': directives.unchanged_required,
    }

    def _create_table_row(self, key, value):
        row = nodes.row()
        key_cell = nodes.paragraph()
        key_cell.append(nodes.strong(text=key))
        row += nodes.entry("", key_cell)
        row += nodes.entry("", nodes.paragraph(text=value))
        return row

    def _create_adr_fields_table(self):
        tgroup = nodes.tgroup('', cols=2)
        tgroup += nodes.colspec(colwidth=30)
        tgroup += nodes.colspec(colwidth=70)

        tbody = nodes.tbody("")
        tbody += self._create_table_row(
            "Creation date",
            self.options.get('creation_date')
        )
        tbody += self._create_table_row(
            "Last update",
            self.options.get('last_update')
        )
        tbody += self._create_table_row(
            "Status",
            self.options.get('status')
        )
        tgroup += tbody

        return nodes.table("", tgroup)

    def _find_nearest_heading(self):
        current_node = self.state.parent
        while current_node:
            if isinstance(current_node, nodes.section):
                return current_node
            current_node = current_node.parent
        return None

    def run(self):
        surrounding_section = self._find_nearest_heading()
        if surrounding_section is not None:
            title = surrounding_section[0]
            title_text = title[0]

        return [
            self._create_adr_fields_table(),
        ]


def setup(app):
    app.add_directive("adr", Adr)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
