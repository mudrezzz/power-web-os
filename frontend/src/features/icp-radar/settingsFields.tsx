import { useTranslation } from 'react-i18next';
import { Badge, Eyebrow } from '../../components/primitives';
import { durationUnitKey, formatDuration, parseDuration } from './model';

// Shared field primitives keep settings blocks visually consistent without coupling them to one large editor file.

export function TextField({ label, onChange, value }: { label: string; onChange: (value: string) => void; value: string }) {
  return (
    <label className="icp-editor-field">
      <span>{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

export function TextAreaField({ label, onChange, value }: { label: string; onChange: (value: string) => void; value: string }) {
  return (
    <label className="icp-editor-field">
      <span>{label}</span>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

export function ArrayTextAreaField({ label, onChange, value }: { label: string; onChange: (value: string[]) => void; value: string[] }) {
  return (
    <TextAreaField
      label={label}
      value={value.join('\n')}
      onChange={(nextValue) => onChange(nextValue.split('\n').map((item) => item.trim()).filter(Boolean))}
    />
  );
}

export function SelectField({
  label,
  onChange,
  optionLabel,
  options,
  value,
}: {
  label: string;
  onChange: (value: string) => void;
  optionLabel?: (value: string) => string;
  options: string[];
  value: string;
}) {
  return (
    <label className="icp-editor-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {optionLabel ? optionLabel(option) : option}
          </option>
        ))}
      </select>
    </label>
  );
}

export function ToggleField({
  checked,
  disabled = false,
  label,
  onChange,
}: {
  checked: boolean;
  disabled?: boolean;
  label: string;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className={`toggle-field${disabled ? ' toggle-field-disabled' : ''}`}>
      <input
        checked={checked}
        disabled={disabled}
        type="checkbox"
        onChange={(event) => {
          if (!disabled) {
            onChange(event.target.checked);
          }
        }}
      />
      <span aria-hidden="true" />
      <strong>{label}</strong>
    </label>
  );
}

export function DurationField({ label, onChange, value }: { label: string; onChange: (value: string) => void; value: string }) {
  const { t } = useTranslation();
  const duration = parseDuration(value);
  return (
    <div className="duration-field">
      <span>{label}</span>
      <TextField
        label={t('icpRadar.settings.durationValue')}
        value={String(duration.amount)}
        onChange={(amount) => onChange(formatDuration(amount, duration.unit))}
      />
      <SelectField
        label={t('icpRadar.settings.durationUnit')}
        options={['days', 'weeks', 'months']}
        value={duration.unit}
        onChange={(unit) => onChange(formatDuration(duration.amount, unit))}
        optionLabel={(option) => t(durationUnitKey(option))}
      />
    </div>
  );
}

export function ListSection({ bounded = false, title, items }: { bounded?: boolean; title: string; items: string[] }) {
  return (
    <section className="icp-detail-section">
      <Eyebrow>{title}</Eyebrow>
      <ul className={`icp-settings-list${bounded ? ' icp-settings-list-bounded' : ''}`}>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

export function NumberField({
  label,
  max,
  min,
  onChange,
  value,
}: {
  label: string;
  max: number;
  min: number;
  onChange: (value: number) => void;
  value: number;
}) {
  return (
    <label className="icp-editor-field">
      <span>{label}</span>
      <input
        max={max}
        min={min}
        type="number"
        value={value}
        onChange={(event) => onChange(Math.min(max, Math.max(min, Number(event.target.value))))}
      />
    </label>
  );
}

export function BooleanPill({ active }: { active: boolean }) {
  const { t } = useTranslation();
  return <Badge tone={active ? 'ally' : 'neutral'}>{active ? t('icpRadar.settings.yes') : t('icpRadar.settings.no')}</Badge>;
}
