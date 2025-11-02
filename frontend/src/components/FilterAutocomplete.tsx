import { Autocomplete, TextField, Chip } from "@mui/material";

interface FilterAutocompleteProps {
  value: string[];
  onChange: (newValue: string[]) => void;
  onDeleteChip?: (value: string) => void;
  options: string[];
  label: string;
  emoji: string;
  chipColor: {
    bg: string;
    text: string;
  };
  disabled?: boolean;
}

export const FilterAutocomplete = ({
  value,
  onChange,
  onDeleteChip,
  options,
  label,
  emoji,
  chipColor,
  disabled = false,
}: FilterAutocompleteProps) => {
  const handleChange = (_: any, newValue: string[]) => {
    if (onDeleteChip && newValue.length < value.length) {
      const removedValue = value.find(v => !newValue.includes(v));
      if (removedValue) {
        onDeleteChip(removedValue);
      }
    }
    onChange(newValue);
  };

  return (
    <Autocomplete
      multiple
      value={value}
      onChange={handleChange}
      options={options}
      renderInput={(params) => (
        <TextField {...params} label={`${emoji} ${label}`} size="small" variant="outlined" />
      )}
      renderTags={(value, getTagProps) =>
        value.map((option, index) => {
          const { key, ...tagProps } = getTagProps({ index });
          return (
            <Chip
              key={key}
              label={option}
              size="small"
              {...tagProps}
              sx={{
                backgroundColor: chipColor.bg,
                color: chipColor.text,
                fontWeight: 500,
                borderRadius: '16px'
              }}
            />
          );
        })
      }
      disabled={disabled}
    />
  );
};
