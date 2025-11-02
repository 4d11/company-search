import { TextField, Typography } from "@mui/material";

interface ChipColors {
  bg: string;
  text: string;
  border: string;
}

interface NumericRangeFilterProps {
  minValue: number | null;
  maxValue: number | null;
  onMinChange: (value: number | null) => void;
  onMaxChange: (value: number | null) => void;
  label: string;
  emoji: string;
  chipColor: ChipColors;
  disabled?: boolean;
}

const formatNumber = (value: number | null): string => {
  if (value === null || value === undefined) return '';
  return value.toLocaleString();
};

const parseNumber = (value: string): number | null => {
  const cleaned = value.replace(/,/g, '');
  const num = Number(cleaned);
  return cleaned && !isNaN(num) ? num : null;
};

export const NumericRangeFilter = ({
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  label,
  emoji,
  chipColor,
  disabled = false,
}: NumericRangeFilterProps) => {
  return (
    <div className={`rounded-xl p-4 border ${chipColor.bg} ${chipColor.border}`}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">{emoji}</span>
        <Typography variant="body2" className={`font-semibold ${chipColor.text}`}>
          {label}
        </Typography>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <TextField
          type="text"
          size="small"
          label="Min"
          placeholder="0"
          value={formatNumber(minValue)}
          onChange={(e) => onMinChange(parseNumber(e.target.value))}
          disabled={disabled}
          sx={{
            backgroundColor: 'white',
            '& .MuiOutlinedInput-root': {
              '&:hover fieldset': {
                borderColor: '#666',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#444',
              }
            }
          }}
        />
        <TextField
          type="text"
          size="small"
          label="Max"
          placeholder="∞"
          value={formatNumber(maxValue)}
          onChange={(e) => onMaxChange(parseNumber(e.target.value))}
          disabled={disabled}
          sx={{
            backgroundColor: 'white',
            '& .MuiOutlinedInput-root': {
              '&:hover fieldset': {
                borderColor: '#666',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#444',
              }
            }
          }}
        />
      </div>
    </div>
  );
};
