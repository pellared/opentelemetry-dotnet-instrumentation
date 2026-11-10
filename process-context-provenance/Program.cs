using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text.Json;

if (args.Length != 3)
{
    Console.Error.WriteLine("Usage: Provenance <application.dll> <application.pdb> <source.cs>");
    return 2;
}

try
{
    var appPath = Path.GetFullPath(args[0]);
    var pdbPath = Path.GetFullPath(args[1]);
    var sourcePath = Path.GetFullPath(args[2]);
    var appBytes = File.ReadAllBytes(appPath);
    var pdbBytes = File.ReadAllBytes(pdbPath);
    var sourceBytes = File.ReadAllBytes(sourcePath);

    using var appStream = new MemoryStream(appBytes, writable: false);
    using var pe = new PEReader(appStream);
    Require(pe.HasMetadata, "The application has no managed metadata.");
    var assembly = pe.GetMetadataReader();
    Require(assembly.IsAssembly, "The application is not a managed assembly.");
    var mvid = assembly.GetGuid(assembly.GetModuleDefinition().Mvid);
    Require(mvid != Guid.Empty, "The application has no module MVID.");

    var codeViewEntries = pe.ReadDebugDirectory()
        .Where(entry => entry.Type == DebugDirectoryEntryType.CodeView).ToArray();
    Require(codeViewEntries.Length == 1,
        $"Expected one PE CodeView entry; found {codeViewEntries.Length}.");
    var codeViewEntry = codeViewEntries[0];
    var codeView = pe.ReadCodeViewDebugDirectoryData(codeViewEntry);

    using var pdbStream = new MemoryStream(pdbBytes, writable: false);
    using var provider = MetadataReaderProvider.FromPortablePdbStream(pdbStream);
    var pdb = provider.GetMetadataReader();
    var pdbHeader = pdb.DebugMetadataHeader
        ?? throw new InvalidOperationException("The PDB has no portable PDB metadata header.");
    var pdbId = new BlobContentId(pdbHeader.Id);
    Require(codeView.Guid == pdbId.Guid && codeViewEntry.Stamp == pdbId.Stamp && codeView.Age == 1,
        "The portable PDB ID does not match the application's PE CodeView GUID/stamp/age.");

    var sourceName = Path.GetFileName(sourcePath);
    var documents = pdb.Documents.Select(handle =>
    {
        var document = pdb.GetDocument(handle);
        return new SourceDocument(
            pdb.GetString(document.Name),
            document.HashAlgorithm.IsNil ? Guid.Empty : pdb.GetGuid(document.HashAlgorithm),
            document.Hash.IsNil ? [] : pdb.GetBlobBytes(document.Hash));
    }).Where(document => FileName(document.Name) == sourceName).ToArray();
    Require(documents.Length > 0, $"No portable PDB document named {sourceName} was found.");

    // An archived source copy can have a different directory. Accept its unique
    // filename only when the PDB does not have the exact supplied source path.
    var exactDocuments = documents.Where(document =>
        NormalizePath(document.Name) == NormalizePath(sourcePath)).ToArray();
    var candidates = exactDocuments.Length > 0 ? exactDocuments : documents;
    Require(candidates.Length == 1,
        $"Ambiguous portable PDB document for {sourceName}: {string.Join(", ", candidates.Select(document => document.Name))}");
    var selected = candidates[0];
    var sha256 = SHA256.HashData(sourceBytes);
    var sha1 = SHA1.HashData(sourceBytes);
    var sha256Guid = new Guid("8829d00f-11b8-4213-878b-770e8597ac16");
    var sha1Guid = new Guid("ff1816ec-aa5e-4d10-87f7-6f4963833460");
    var algorithm = selected.HashAlgorithmGuid == sha256Guid ? "SHA256"
        : selected.HashAlgorithmGuid == sha1Guid ? "SHA1"
        : throw new InvalidOperationException(
            $"Unsupported portable PDB document hash algorithm: {selected.HashAlgorithmGuid}");
    var sourceHash = algorithm == "SHA256" ? sha256 : sha1;
    Require(CryptographicOperations.FixedTimeEquals(selected.Hash, sourceHash),
        $"Source bytes do not match portable PDB document {selected.Name}: {algorithm} expected {Hex(selected.Hash)}, supplied {Hex(sourceHash)}.");

    Console.WriteLine(JsonSerializer.Serialize(new
    {
        schemaVersion = 1,
        appPath,
        appSha256 = Hex(SHA256.HashData(appBytes)),
        assemblyName = assembly.GetString(assembly.GetAssemblyDefinition().Name),
        assemblyMvid = mvid,
        pdbPath,
        pdbSha256 = Hex(SHA256.HashData(pdbBytes)),
        peCodeViewPdbGuid = codeView.Guid,
        peCodeViewPdbStamp = codeViewEntry.Stamp,
        peCodeViewPdbAge = codeView.Age,
        peCodeViewPdbPath = codeView.Path,
        portablePdbGuid = pdbId.Guid,
        portablePdbStamp = pdbId.Stamp,
        pdbMatchesApplication = true,
        sourcePath,
        sourceSha256 = Hex(sha256),
        sourceSha1 = Hex(sha1),
        documentName = selected.Name,
        documentSelection = exactDocuments.Length > 0 ? "exactPath" : "uniqueFileName",
        documentHashAlgorithmGuid = selected.HashAlgorithmGuid,
        documentHashAlgorithm = algorithm,
        documentHash = Hex(selected.Hash),
        sourceMatchesDocument = true,
    }, new JsonSerializerOptions { WriteIndented = true }));
    return 0;
}
catch (Exception error) when (error is IOException or UnauthorizedAccessException
    or BadImageFormatException or InvalidOperationException or ArgumentException
    or CryptographicException)
{
    Console.Error.WriteLine($"Provenance validation failed: {error.Message}");
    return 1;
}

static void Require(bool condition, string message)
{
    if (!condition)
    {
        throw new InvalidOperationException(message);
    }
}

static string Hex(byte[] bytes) => Convert.ToHexString(bytes).ToLowerInvariant();
static string NormalizePath(string value) => value.Replace('\\', '/');
static string FileName(string value) => NormalizePath(value).Split('/')[^1];

sealed record SourceDocument(string Name, Guid HashAlgorithmGuid, byte[] Hash);
