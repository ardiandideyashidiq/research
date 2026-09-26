import os, subprocess

META = {
 'hukum-perdata': ("Hukum Perdata & Perikatan",
   "Doktrin hukum perdata Indonesia dari buku III dan IV Burgerlijk Wetboek: "
   "sumber perikatan, wanprestasi, ganti rugi, dan rezim hak atas benda."),
 'hukum-keluarga': ("Hukum Keluarga & Perkawinan",
   "Doktrin hukum perkawinan Indonesia: dasar UU 1/1974 sebagai diubah "
   "UU 16/2019, rukun dan syarat, serta Kompilasi Hukum Islam."),
 'hukum-adat': ("Hukum Adat & Masyarakat Adat",
   "Doktrin kedudukan hukum adat dalam tatanan hukum positif Indonesia: "
   "pengakuan bersyarat menurut UUPA 1960 dan relasi peradilan adat."),
 'hukum-tata-negara': ("Hukum Tata Negara & Konstitusi",
   "Doktrin struktural UUD 1945: kedudukan Pembukaan, evolusi amandemen, "
   "pengelompokan hak konstitusional, dan teknik klausul delegasi."),
 'hukum-lingkungan': ("Hukum Lingkungan & Sumber Daya Alam",
   "Doktrin UU 32/2009: asas perlindungan lingkungan, hak atas lingkungan "
   "yang sehat, pengelolaan sumber daya alam, serta Amdal dan perizinan "
   "lingkungan."),
 'ham': ("Hak Asasi Manusia",
   "Doktrin hak asasi manusia: landasan konstitusional, ranah sosial-ekonomi, "
   "kedudukan kelompok rentan, dan instrumen pelindungan."),
}

DESC = {
 'hukum-perdata/perikatan.md': ("Hukum Perikatan", "sumber perikatan menurut Pasal 1233, syarat sah perjanjian, wanprestasi, keadaan memaksa, dan ganti rugi"),
 'hukum-perdata/harta-benda.md': ("Hukum Benda", "klasifikasi benda bergerak dan tidak bergerak, asas-asas hukum benda, struktur hak milik, dan rezim pertanahan menurut UUPA"),
 'hukum-keluarga/perkawinan.md': ("Hukum Perkawinan", "dasar UU 1/1974, rukun dan syarat perkawinan menurut fikih nikah dan KHI, pencatatan nikah, serta perkawinan campuran"),
 'hukum-adat/kedudukan-hukum-adat.md': ("Kedudukan Hukum Adat", "pengakuan bersyarat dalam UUPA 1960, fungsi perdata dalam KUHPerdata, dan relasi peradilan adat"),
 'hukum-tata-negara/uud-1945.md': ("Struktur UUD 1945", "kedudukan Pembukaan sebagai norma fundamental, evolusi amandemen, hak konstitusional, klausul delegasi, dan open legal policy"),
 'hukum-lingkungan/hukum-lingkungan.md': ("Hukum Lingkungan", "asas perlindungan lingkungan, hak konstitusional atas lingkungan yang sehat, internalisasi biaya pencemar, dan keadilan antar generasi"),
 'hukum-lingkungan/pengelolaan-sda.md': ("Pengelolaan SDA", "rezim pengelolaan sumber daya alam, konservasi, keanekaragaman hayati, dan hak hutan adat"),
 'hukum-lingkungan/amdal-dan-proses-permitasan.md': ("Amdal dan Perizinan", "Amdal, ANDAL, UKL-UPL, persetujuan lingkungan, dan sanksi administratif"),
 'ham/ham-konstitusional.md': ("HAM Konstitusional", "HAM dalam UUD 1945, Piagam PBB, Deklarasi Universal, evolusi konstitusional, dan pengujian hak konstitusional"),
 'ham/ham-ranah-sosial.md': ("HAM Sosial-Ekonomi", "hak atas kesehatan, pendidikan, pekerjaan, rumah, jaminan sosial, dan kewajiban positif negara"),
 'ham/ham-individu-kelompok-rentan.md': ("Kelompok Rentan", "anak, perempuan, penyandang disabilitas, minoritas suku dan agama, pekerja migran, dan narapidana"),
}

for folder, (title, desc) in META.items():
    d = os.path.join('knowledge', folder)
    files = sorted(x for x in os.listdir(d) if x.endswith('.md') and x != 'README.md')
    lines = [
        '---',
        f'title: Pustaka {title}',
        'description: >-',
        f'  {desc}',
        '---',
        '',
        f'# Pustaka {title}',
        '',
        'Disintil dari korpus buku',
        '`/home/rd/Documents/organized/01-kuliah/hukum/topikal/topical/`.',
        'Sebelum mengutip pasal dari file di sini, baca',
        '[`CATATAN-KORPUS-2026.md`](../CATATAN-KORPUS-2026.md) untuk catatan',
        'status instrumen dan jebakan korpus.',
        '',
        '## Isi',
        '',
    ]
    for fn in files:
        key = f'{folder}/{fn}'
        label, detail = DESC.get(key, (fn[:-3].replace('-', ' ').title(), ''))
        lines.append(f'- <a href="./{fn}">`{fn}`</a>')
        lines.append(f'  — **{label}**: {detail}.')
        lines.append('')
    open(os.path.join(d, 'README.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    print(f'{folder}: {len(files)} file(s) indexed')
