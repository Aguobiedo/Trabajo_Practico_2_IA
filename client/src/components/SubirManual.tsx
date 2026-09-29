import { useRef, useState, type DragEvent, type FormEvent } from "react";
import { AlertTriangle, CloudUpload, FileText, X } from "lucide-react";
import { api } from "../api";
import type { ManualSubido } from "../types";

const EXTENSIONES = [".md", ".txt", ".pdf"];
const MAX_BYTES = 10 * 1024 * 1024; // mismo límite que el server

function validar(archivo: File): string | null {
  const nombre = archivo.name.toLowerCase();
  if (!EXTENSIONES.some((ext) => nombre.endsWith(ext))) return "Formato no admitido. Subí un archivo .md, .txt o .pdf";
  if (archivo.size > MAX_BYTES) return "El archivo supera los 10 MB";
  return null;
}

function tamano(bytes: number) {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

interface Props {
  onSubido: (manual: ManualSubido) => void;
  onCerrar: () => void;
}

export default function SubirManual({ onSubido, onCerrar }: Props) {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [modelo, setModelo] = useState("");
  const [equipo, setEquipo] = useState("");
  const [alias, setAlias] = useState("");
  const [arrastrando, setArrastrando] = useState(false);
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputArchivo = useRef<HTMLInputElement>(null);

  const elegir = (f: File | undefined) => {
    if (!f) return;
    const problema = validar(f);
    setError(problema);
    setArchivo(problema ? null : f);
  };

  const quitar = () => {
    setArchivo(null);
    if (inputArchivo.current) inputArchivo.current.value = "";
  };

  const alSoltar = (e: DragEvent) => {
    e.preventDefault();
    setArrastrando(false);
    elegir(e.dataTransfer.files[0]);
  };

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    if (!archivo) return;
    const datos = new FormData();
    datos.append("archivo", archivo);
    datos.append("modelo", modelo);
    datos.append("equipo", equipo);
    datos.append("alias", alias);

    setSubiendo(true);
    setError(null);
    try {
      onSubido(await api.subirManual(datos));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubiendo(false);
    }
  };

  // lo que usará el server si el campo queda vacío (sin contar el encabezado del archivo)
  const nombreBase = archivo?.name.replace(/\.[^.]+$/, "") ?? "";

  return (
    <form className="tarjeta form-subida" onSubmit={enviar}>
      <div className="form-subida-cabecera">
        <div>
          <h3>Agregar manual</h3>
          <p className="tenue">Se guarda en data/manuales y se indexa al subirlo. Si el archivo ya existe, se reemplaza.</p>
        </div>
        <button type="button" className="boton-icono" onClick={onCerrar} aria-label="Cerrar" disabled={subiendo}>
          <X size={18} />
        </button>
      </div>

      {archivo ? (
        <div className="archivo-elegido">
          <FileText size={22} />
          <div>
            <strong>{archivo.name}</strong>
            <small className="tenue">{tamano(archivo.size)}</small>
          </div>
          <button type="button" className="boton-icono" onClick={quitar} aria-label="Quitar archivo" disabled={subiendo}>
            <X size={16} />
          </button>
        </div>
      ) : (
        <label
          className={`zona-carga ${arrastrando ? "arrastrando" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setArrastrando(true);
          }}
          onDragLeave={() => setArrastrando(false)}
          onDrop={alSoltar}
        >
          <CloudUpload size={30} />
          <span>
            <strong>Arrastrá un archivo</strong> o hacé clic para elegirlo
          </span>
          <small className="tenue">MD, TXT o PDF · hasta 10 MB</small>
          <input
            ref={inputArchivo}
            type="file"
            accept={EXTENSIONES.join(",")}
            onChange={(e) => elegir(e.target.files?.[0])}
          />
        </label>
      )}

      <div className="campos">
        <label className="campo">
          <span>Modelo</span>
          <input value={modelo} onChange={(e) => setModelo(e.target.value)} placeholder={nombreBase || "Ej.: CT-75"} />
        </label>
        <label className="campo">
          <span>Equipo</span>
          <input
            value={equipo}
            onChange={(e) => setEquipo(e.target.value)}
            placeholder={modelo || nombreBase || "Ej.: Compresor de tornillo"}
          />
        </label>
        <label className="campo">
          <span>Alias</span>
          <input value={alias} onChange={(e) => setAlias(e.target.value)} placeholder="Ej.: compresor, aeron" />
        </label>
      </div>
      <p className="tenue ayuda">
        Opcionales: si quedan vacíos se usa el encabezado del archivo (<code>modelo:</code>, <code>equipo:</code>,{" "}
        <code>alias:</code>) o el nombre del archivo. El modelo y los alias (separados por coma) sirven para detectar de
        qué máquina habla cada pregunta.
      </p>

      {error && (
        <div className="aviso aviso-error">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="acciones">
        <button type="button" className="boton-secundario" onClick={onCerrar} disabled={subiendo}>
          Cancelar
        </button>
        <button type="submit" className="boton-primario" disabled={!archivo || subiendo}>
          <CloudUpload size={16} /> {subiendo ? "Indexando…" : "Subir e indexar"}
        </button>
      </div>
    </form>
  );
}
