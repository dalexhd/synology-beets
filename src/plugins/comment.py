# comment.py
import time
from beets.plugins import BeetsPlugin
from beets.library import Item
from beets.dbcore import types

class CommentPlugin(BeetsPlugin):
    """
    A custom plugin that appends certain fields to the comment tag.
    """

    data_source = "CommentPlugin"  # For logging references

    # If you want typed columns, uncomment and define them here:
    # item_types = {
    #     'spotify_track_popularity': types.INTEGER,
    #     'spotify_tempo': types.FLOAT,
    #     # etc.
    # }

    def __init__(self):
        super().__init__()
        # Merge our default config with user overrides
        self.config.add({
            'fields': [],
            'comment_separator': ', ',
            'existing_comment_separator': ' | ',
            'threshold_popularity': 0,
            'set_bpm_field': False,
        })

        # Convert the config to a string safely (no placeholders)
        config_str = repr(self.config.flatten())
        self._log.debug(
            "{0}.init: plugin loaded with config: {1}"
            .format(self.data_source, config_str)
        )

        # Register the 'write' event, so we run just before beets writes tags
        self.register_listener('write', self.write_event)

    def write_event(self, item: Item):
        """
        Called before beets writes metadata to the file.
        We'll check our plugin config to decide how/what to write.
        """
        # Convert item’s fields to a repr string first.
        # This way, we don't risk `.format()` interpreting braces as placeholders.
        # Gather all fields in a string
        all_fields_str = "\n".join(
            ["'{0}': '{1}'".format(key, val) for key, val in item.items()]
        )

        # Log all fields individually
        self._log.debug("{0}.write_event: all item fields =>\n{1}"
                        .format(self.data_source, all_fields_str))


        fields_list = self.config['fields'].get(list)
        comment_sep = self.config['comment_separator'].as_str()
        existing_sep = self.config['existing_comment_separator'].as_str()
        threshold_pop = self.config['threshold_popularity'].as_number()
        set_bpm = self.config['set_bpm_field'].get(bool)

        # Logging with .format() but no curly braces in the dictionary
        self._log.debug(
            "{0}.write_event: triggered for item path='{1}', title='{2}'"
            .format(self.data_source, item.path, item.title)
        )
        self._log.debug(
            "{0}.write_event: fields_list={1}, threshold_popularity={2}, set_bpm_field={3}"
            .format(self.data_source, fields_list, threshold_pop, set_bpm)
        )

        # Try to avoid curly braces from the dict, so do str() first
        # rather than passing to .format() directly
        item_dict_str = str(dict(item.items()))
        self._log.debug(
            "{0}.write_event: item fields before transformation: {1}"
            .format(self.data_source, item_dict_str)
        )

        comment_parts = []

        # Check each field from our config
        for f in fields_list:
            if f in item and item[f]:
                value = item[f]
                self._log.debug(
                    "{0}.write_event: found field '{1}' with value='{2}'"
                    .format(self.data_source, f, value)
                )
                if f == 'spotify_track_popularity':
                    pop_value = float(value)
                    if pop_value < threshold_pop:
                        self._log.debug(
                            "{0}.write_event: skipping popularity {1} < threshold {2}"
                            .format(self.data_source, pop_value, threshold_pop)
                        )
                        continue
                    comment_parts.append("{0}={1}".format(f, pop_value))

                elif f == 'spotify_tempo':
                    comment_parts.append("{0}={1}".format(f, value))
                    if set_bpm:
                        try:
                            item['bpm'] = float(value)
                            self._log.debug(
                                "{0}.write_event: set item['bpm'] = {1}"
                                .format(self.data_source, value)
                            )
                        except ValueError:
                            self._log.warning(
                                "{0}.write_event: could not convert '{1}' to float for bpm"
                                .format(self.data_source, value)
                            )
                else:
                    # For other fields, just add them to the comment
                    comment_parts.append("{0}={1}".format(f, value))
            else:
                self._log.debug(
                    "{0}.write_event: field '{1}' not found or empty on item '{2}'"
                    .format(self.data_source, f, item.title)
                )

        existing_comment = item.get('comment', '').strip()
        self._log.debug(
            "{0}.write_event: existing_comment='{1}'"
            .format(self.data_source, existing_comment)
        )

        final_comment_parts = []
        if existing_comment:
            final_comment_parts.append(existing_comment)
        if comment_parts:
            final_comment_parts.append(comment_sep.join(comment_parts))

        final_comment = existing_sep.join(final_comment_parts) if final_comment_parts else ""

        item['comment'] = final_comment

        self._log.info(
            "{0}.write_event: setting comment on '{1}' -> '{2}'"
            .format(self.data_source, item.title, final_comment)
        )